#!/usr/bin/env python3
"""
Session Manager
Handles user sessions, authentication, and session state management for the Streamlit UI.
"""

import os
import json
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import streamlit as st

class SessionManager:
    """
    Manages user sessions for the Clinical NLQ Streamlit application.
    Handles session creation, validation, cleanup, and persistence.
    """
    
    def __init__(self, session_dir: str = "d:/projects/healthca/logs/sessions"):
        """
        Initialize the session manager.
        
        Args:
            session_dir: Directory to store session files
        """
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Session configuration
        self.session_timeout = timedelta(hours=2)  # 2 hour timeout
        self.max_sessions_per_user = 5
        self.cleanup_interval = timedelta(hours=1)
        
        # Last cleanup time
        self.last_cleanup = datetime.now()
    
    def create_session(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new user session.
        
        Args:
            user_id: Optional user identifier
            
        Returns:
            Dict containing session information
        """
        session_id = str(uuid.uuid4())
        session_start = datetime.now()
        
        session_data = {
            'session_id': session_id,
            'user_id': user_id or 'anonymous',
            'created_at': session_start.isoformat(),
            'last_activity': session_start.isoformat(),
            'query_count': 0,
            'success_count': 0,
            'error_count': 0,
            'total_processing_time': 0.0,
            'preferences': {
                'show_sql': True,
                'show_metadata': False,
                'default_format': 'table',
                'max_rows_display': 50,
                'theme': 'light'
            },
            'query_history': [],
            'error_history': [],
            'ip_address': self._get_client_ip(),
            'user_agent': self._get_user_agent(),
            'status': 'active'
        }
        
        # Save session to file
        self._save_session(session_id, session_data)
        
        return session_data
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data by session ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None if not found/expired
        """
        session_file = self.session_dir / f"{session_id}.json"
        
        if not session_file.exists():
            return None
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Check if session is expired
            last_activity = datetime.fromisoformat(session_data['last_activity'])
            if datetime.now() - last_activity > self.session_timeout:
                self._expire_session(session_id)
                return None
            
            return session_data
            
        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
            return None
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update session data.
        
        Args:
            session_id: Session identifier
            updates: Dictionary of updates to apply
            
        Returns:
            True if successful, False otherwise
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return False
        
        # Update last activity
        session_data['last_activity'] = datetime.now().isoformat()
        
        # Apply updates
        for key, value in updates.items():
            if key in session_data:
                session_data[key] = value
            elif key == 'preferences' and isinstance(value, dict):
                session_data['preferences'].update(value)
        
        # Save updated session
        return self._save_session(session_id, session_data)
    
    def add_query_to_history(self, session_id: str, query_data: Dict[str, Any]) -> bool:
        """
        Add a query to the session history.
        
        Args:
            session_id: Session identifier
            query_data: Query information to store
            
        Returns:
            True if successful, False otherwise
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return False
        
        # Prepare query record
        query_record = {
            'timestamp': datetime.now().isoformat(),
            'nlq': query_data.get('nlq', ''),
            'generated_sql': query_data.get('generated_sql', ''),
            'success': query_data.get('success', False),
            'error': query_data.get('error', ''),
            'rows_returned': query_data.get('rows_returned', 0),
            'processing_time': query_data.get('processing_time', 0.0),
            'output_formats': query_data.get('output_formats', []),
            'query_id': query_data.get('query_id', '')
        }
        
        # Add to history (keep last 100 queries)
        session_data['query_history'].append(query_record)
        if len(session_data['query_history']) > 100:
            session_data['query_history'] = session_data['query_history'][-100:]
        
        # Update session statistics
        session_data['query_count'] += 1
        if query_record['success']:
            session_data['success_count'] += 1
        else:
            session_data['error_count'] += 1
        
        session_data['total_processing_time'] += query_record['processing_time']
        
        return self.update_session(session_id, session_data)
    
    def add_error_to_history(self, session_id: str, error_data: Dict[str, Any]) -> bool:
        """
        Add an error to the session error history.
        
        Args:
            session_id: Session identifier
            error_data: Error information to store
            
        Returns:
            True if successful, False otherwise
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return False
        
        # Prepare error record
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_data.get('error_type', 'unknown'),
            'error_message': error_data.get('error_message', ''),
            'context': error_data.get('context', {}),
            'stack_trace': error_data.get('stack_trace', ''),
            'user_action': error_data.get('user_action', ''),
            'resolved': False
        }
        
        # Add to error history (keep last 50 errors)
        session_data['error_history'].append(error_record)
        if len(session_data['error_history']) > 50:
            session_data['error_history'] = session_data['error_history'][-50:]
        
        return self.update_session(session_id, session_data)
    
    def get_session_statistics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session statistics.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session statistics or None if session not found
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return None
        
        created_at = datetime.fromisoformat(session_data['created_at'])
        last_activity = datetime.fromisoformat(session_data['last_activity'])
        session_duration = last_activity - created_at
        
        stats = {
            'session_id': session_id,
            'user_id': session_data['user_id'],
            'created_at': created_at,
            'last_activity': last_activity,
            'session_duration': session_duration,
            'query_count': session_data['query_count'],
            'success_count': session_data['success_count'],
            'error_count': session_data['error_count'],
            'success_rate': session_data['success_count'] / max(session_data['query_count'], 1),
            'avg_processing_time': session_data['total_processing_time'] / max(session_data['query_count'], 1),
            'total_processing_time': session_data['total_processing_time'],
            'queries_per_minute': session_data['query_count'] / max(session_duration.total_seconds() / 60, 1),
            'status': session_data['status']
        }
        
        return stats
    
    def list_active_sessions(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all active sessions.
        
        Args:
            user_id: Optional filter by user ID
            
        Returns:
            List of active session statistics
        """
        active_sessions = []
        
        for session_file in self.session_dir.glob("*.json"):
            session_id = session_file.stem
            session_data = self.get_session(session_id)
            
            if session_data and session_data['status'] == 'active':
                if user_id is None or session_data['user_id'] == user_id:
                    stats = self.get_session_statistics(session_id)
                    if stats:
                        active_sessions.append(stats)
        
        # Sort by last activity (most recent first)
        active_sessions.sort(key=lambda x: x['last_activity'], reverse=True)
        
        return active_sessions
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        if datetime.now() - self.last_cleanup < self.cleanup_interval:
            return 0
        
        cleaned_count = 0
        current_time = datetime.now()
        
        for session_file in self.session_dir.glob("*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                last_activity = datetime.fromisoformat(session_data['last_activity'])
                
                # Check if session is expired
                if current_time - last_activity > self.session_timeout:
                    session_file.unlink()  # Delete the file
                    cleaned_count += 1
                    
            except Exception as e:
                print(f"Error cleaning up session {session_file}: {e}")
                # Delete corrupted session files
                try:
                    session_file.unlink()
                    cleaned_count += 1
                except:
                    pass
        
        self.last_cleanup = current_time
        return cleaned_count
    
    def expire_session(self, session_id: str) -> bool:
        """
        Manually expire a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        return self._expire_session(session_id)
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all sessions for a specific user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of user sessions
        """
        user_sessions = []
        
        for session_file in self.session_dir.glob("*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                if session_data['user_id'] == user_id:
                    stats = self.get_session_statistics(session_file.stem)
                    if stats:
                        user_sessions.append(stats)
                        
            except Exception as e:
                print(f"Error reading session {session_file}: {e}")
        
        # Sort by creation time (most recent first)
        user_sessions.sort(key=lambda x: x['created_at'], reverse=True)
        
        return user_sessions
    
    def _save_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """
        Save session data to file.
        
        Args:
            session_id: Session identifier
            session_data: Session data to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_file = self.session_dir / f"{session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving session {session_id}: {e}")
            return False
    
    def _expire_session(self, session_id: str) -> bool:
        """
        Expire a session by deleting its file.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_file = self.session_dir / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
            return True
        except Exception as e:
            print(f"Error expiring session {session_id}: {e}")
            return False
    
    def _get_client_ip(self) -> str:
        """Get client IP address from Streamlit context."""
        try:
            # Try to get IP from Streamlit context
            if hasattr(st, 'session_state') and hasattr(st.session_state, 'client_ip'):
                return st.session_state.client_ip
            return 'unknown'
        except:
            return 'unknown'
    
    def _get_user_agent(self) -> str:
        """Get user agent from Streamlit context."""
        try:
            # Try to get user agent from headers
            return 'streamlit-browser'
        except:
            return 'unknown'
    
    def export_session_data(self, session_id: str, format: str = 'json') -> Optional[str]:
        """
        Export session data in specified format.
        
        Args:
            session_id: Session identifier
            format: Export format ('json', 'csv')
            
        Returns:
            Exported data as string or None if failed
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return None
        
        try:
            if format.lower() == 'json':
                return json.dumps(session_data, indent=2, ensure_ascii=False)
            
            elif format.lower() == 'csv':
                # Export query history as CSV
                import pandas as pd
                
                if session_data['query_history']:
                    df = pd.DataFrame(session_data['query_history'])
                    return df.to_csv(index=False)
                else:
                    return "No query history available"
            
            else:
                return None
                
        except Exception as e:
            print(f"Error exporting session data: {e}")
            return None
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get summary of all sessions.
        
        Returns:
            Summary statistics for all sessions
        """
        total_sessions = 0
        active_sessions = 0
        total_queries = 0
        total_errors = 0
        total_processing_time = 0.0
        
        for session_file in self.session_dir.glob("*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                total_sessions += 1
                
                if session_data['status'] == 'active':
                    last_activity = datetime.fromisoformat(session_data['last_activity'])
                    if datetime.now() - last_activity <= self.session_timeout:
                        active_sessions += 1
                
                total_queries += session_data['query_count']
                total_errors += session_data['error_count']
                total_processing_time += session_data['total_processing_time']
                
            except Exception as e:
                print(f"Error reading session {session_file}: {e}")
        
        return {
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'total_queries': total_queries,
            'total_errors': total_errors,
            'total_processing_time': total_processing_time,
            'avg_queries_per_session': total_queries / max(total_sessions, 1),
            'overall_success_rate': (total_queries - total_errors) / max(total_queries, 1),
            'avg_processing_time': total_processing_time / max(total_queries, 1)
        }