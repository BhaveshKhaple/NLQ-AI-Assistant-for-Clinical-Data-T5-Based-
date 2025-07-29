#!/usr/bin/env python3
"""
Activity Logger
Comprehensive activity logging for the Streamlit UI including user interactions,
query processing, errors, and performance metrics.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import pandas as pd
from logging.handlers import RotatingFileHandler

class ActivityLogger:
    """
    Comprehensive activity logger for the Clinical NLQ Streamlit application.
    Tracks user interactions, query processing, errors, and system performance.
    """
    
    def __init__(self, log_dir: str = "d:/projects/healthca/logs"):
        """
        Initialize the activity logger.
        
        Args:
            log_dir: Directory to store log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Log rotation settings
        self.max_log_size = 10 * 1024 * 1024  # 10MB
        self.backup_count = 5
        
        # Initialize different loggers
        self.activity_logger = self._setup_activity_logger()
        self.performance_logger = self._setup_performance_logger()
        self.error_logger = self._setup_error_logger()
        self.user_interaction_logger = self._setup_user_interaction_logger()
        
        # Activity tracking
        self.session_activities = {}
        self.performance_metrics = []
    
    def _setup_activity_logger(self) -> logging.Logger:
        """Setup the main activity logger."""
        logger = logging.getLogger('clinical_nlq_activity')
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        
        # File handler with rotation
        handler = RotatingFileHandler(
            self.log_dir / 'activity.log',
            maxBytes=self.max_log_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _setup_performance_logger(self) -> logging.Logger:
        """Setup the performance metrics logger."""
        logger = logging.getLogger('clinical_nlq_performance')
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        
        handler = RotatingFileHandler(
            self.log_dir / 'performance.log',
            maxBytes=self.max_log_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - PERFORMANCE - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _setup_error_logger(self) -> logging.Logger:
        """Setup the error logger."""
        logger = logging.getLogger('clinical_nlq_errors')
        logger.setLevel(logging.ERROR)
        logger.handlers.clear()
        
        handler = RotatingFileHandler(
            self.log_dir / 'ui_errors.log',
            maxBytes=self.max_log_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - ERROR - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _setup_user_interaction_logger(self) -> logging.Logger:
        """Setup the user interaction logger."""
        logger = logging.getLogger('clinical_nlq_interactions')
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        
        handler = RotatingFileHandler(
            self.log_dir / 'user_interactions.log',
            maxBytes=self.max_log_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - INTERACTION - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def log_activity(self, 
                    session_id: str,
                    activity_type: str,
                    details: Dict[str, Any],
                    success: bool = True,
                    user_id: Optional[str] = None) -> None:
        """
        Log a general activity.
        
        Args:
            session_id: Session identifier
            activity_type: Type of activity (e.g., 'query_start', 'query_complete')
            details: Activity details
            success: Whether the activity was successful
            user_id: Optional user identifier
        """
        activity_record = {
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'user_id': user_id or 'anonymous',
            'activity_type': activity_type,
            'success': success,
            'details': details
        }
        
        # Log to file
        log_message = json.dumps(activity_record, ensure_ascii=False)
        self.activity_logger.info(log_message)
        
        # Store in memory for session tracking
        if session_id not in self.session_activities:
            self.session_activities[session_id] = []
        
        self.session_activities[session_id].append(activity_record)
        
        # Keep only last 100 activities per session
        if len(self.session_activities[session_id]) > 100:
            self.session_activities[session_id] = self.session_activities[session_id][-100:]
    
    def log_query_processing(self,
                           session_id: str,
                           query_id: str,
                           nlq: str,
                           generated_sql: str,
                           success: bool,
                           processing_time: float,
                           rows_returned: int = 0,
                           error_message: str = None,
                           user_id: Optional[str] = None) -> None:
        """
        Log query processing details.
        
        Args:
            session_id: Session identifier
            query_id: Query identifier
            nlq: Natural language query
            generated_sql: Generated SQL query
            success: Whether query was successful
            processing_time: Total processing time in seconds
            rows_returned: Number of rows returned
            error_message: Error message if failed
            user_id: Optional user identifier
        """
        query_record = {
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'user_id': user_id or 'anonymous',
            'query_id': query_id,
            'nlq': nlq,
            'generated_sql': generated_sql,
            'success': success,
            'processing_time': processing_time,
            'rows_returned': rows_returned,
            'error_message': error_message,
            'nlq_length': len(nlq),
            'sql_length': len(generated_sql) if generated_sql else 0
        }
        
        # Log to activity logger
        self.log_activity(
            session_id=session_id,
            activity_type='query_processing',
            details=query_record,
            success=success,
            user_id=user_id
        )
        
        # Log performance metrics
        self.log_performance_metric(
            metric_type='query_processing',
            session_id=session_id,
            metrics={
                'processing_time': processing_time,
                'rows_returned': rows_returned,
                'nlq_length': len(nlq),
                'sql_length': len(generated_sql) if generated_sql else 0,
                'success': success
            }
        )
    
    def log_user_interaction(self,
                           session_id: str,
                           interaction_type: str,
                           component: str,
                           details: Dict[str, Any],
                           user_id: Optional[str] = None) -> None:
        """
        Log user interface interactions.
        
        Args:
            session_id: Session identifier
            interaction_type: Type of interaction (click, input, selection, etc.)
            component: UI component involved
            details: Interaction details
            user_id: Optional user identifier
        """
        interaction_record = {
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'user_id': user_id or 'anonymous',
            'interaction_type': interaction_type,
            'component': component,
            'details': details
        }
        
        log_message = json.dumps(interaction_record, ensure_ascii=False)
        self.user_interaction_logger.info(log_message)
        
        # Also log as general activity
        self.log_activity(
            session_id=session_id,
            activity_type='user_interaction',
            details=interaction_record,
            success=True,
            user_id=user_id
        )
    
    def log_error(self,
                 session_id: str,
                 error_type: str,
                 error_message: str,
                 context: Dict[str, Any],
                 stack_trace: str = None,
                 user_id: Optional[str] = None) -> None:
        """
        Log error occurrences.
        
        Args:
            session_id: Session identifier
            error_type: Type of error
            error_message: Error message
            context: Error context information
            stack_trace: Optional stack trace
            user_id: Optional user identifier
        """
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'user_id': user_id or 'anonymous',
            'error_type': error_type,
            'error_message': error_message,
            'context': context,
            'stack_trace': stack_trace
        }
        
        log_message = json.dumps(error_record, ensure_ascii=False)
        self.error_logger.error(log_message)
        
        # Also log as general activity
        self.log_activity(
            session_id=session_id,
            activity_type='error',
            details=error_record,
            success=False,
            user_id=user_id
        )
    
    def log_performance_metric(self,
                             metric_type: str,
                             session_id: str,
                             metrics: Dict[str, Any]) -> None:
        """
        Log performance metrics.
        
        Args:
            metric_type: Type of performance metric
            session_id: Session identifier
            metrics: Performance metrics dictionary
        """
        performance_record = {
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'metric_type': metric_type,
            'metrics': metrics
        }
        
        log_message = json.dumps(performance_record, ensure_ascii=False)
        self.performance_logger.info(log_message)
        
        # Store in memory for analysis
        self.performance_metrics.append(performance_record)
        
        # Keep only last 1000 metrics
        if len(self.performance_metrics) > 1000:
            self.performance_metrics = self.performance_metrics[-1000:]
    
    def log_system_event(self,
                        event_type: str,
                        details: Dict[str, Any],
                        severity: str = 'info') -> None:
        """
        Log system-level events.
        
        Args:
            event_type: Type of system event
            details: Event details
            severity: Event severity (info, warning, error)
        """
        system_record = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'severity': severity,
            'details': details
        }
        
        log_message = json.dumps(system_record, ensure_ascii=False)
        
        if severity == 'error':
            self.error_logger.error(log_message)
        else:
            self.activity_logger.info(log_message)
    
    def get_session_activities(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get activities for a specific session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of session activities
        """
        return self.session_activities.get(session_id, [])
    
    def get_recent_activities(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent activities across all sessions.
        
        Args:
            limit: Maximum number of activities to return
            
        Returns:
            List of recent activities
        """
        all_activities = []
        
        for session_activities in self.session_activities.values():
            all_activities.extend(session_activities)
        
        # Sort by timestamp (most recent first)
        all_activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return all_activities[:limit]
    
    def get_performance_summary(self, 
                              session_id: Optional[str] = None,
                              time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """
        Get performance summary statistics.
        
        Args:
            session_id: Optional session filter
            time_window: Optional time window filter
            
        Returns:
            Performance summary statistics
        """
        # Filter metrics
        filtered_metrics = self.performance_metrics
        
        if session_id:
            filtered_metrics = [m for m in filtered_metrics if m['session_id'] == session_id]
        
        if time_window:
            cutoff_time = datetime.now() - time_window
            filtered_metrics = [
                m for m in filtered_metrics 
                if datetime.fromisoformat(m['timestamp']) >= cutoff_time
            ]
        
        if not filtered_metrics:
            return {
                'total_metrics': 0,
                'query_metrics': {},
                'system_metrics': {}
            }
        
        # Analyze query processing metrics
        query_metrics = [m for m in filtered_metrics if m['metric_type'] == 'query_processing']
        
        query_summary = {}
        if query_metrics:
            processing_times = [m['metrics']['processing_time'] for m in query_metrics]
            rows_returned = [m['metrics']['rows_returned'] for m in query_metrics]
            success_count = sum(1 for m in query_metrics if m['metrics']['success'])
            
            query_summary = {
                'total_queries': len(query_metrics),
                'success_count': success_count,
                'success_rate': success_count / len(query_metrics),
                'avg_processing_time': sum(processing_times) / len(processing_times),
                'min_processing_time': min(processing_times),
                'max_processing_time': max(processing_times),
                'avg_rows_returned': sum(rows_returned) / len(rows_returned),
                'total_rows_returned': sum(rows_returned)
            }
        
        return {
            'total_metrics': len(filtered_metrics),
            'query_metrics': query_summary,
            'time_window': time_window.total_seconds() if time_window else None,
            'session_id': session_id
        }
    
    def get_error_summary(self, 
                         session_id: Optional[str] = None,
                         time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """
        Get error summary statistics.
        
        Args:
            session_id: Optional session filter
            time_window: Optional time window filter
            
        Returns:
            Error summary statistics
        """
        # Get error activities
        error_activities = []
        
        if session_id:
            activities = self.session_activities.get(session_id, [])
        else:
            activities = []
            for session_activities in self.session_activities.values():
                activities.extend(session_activities)
        
        # Filter by time window
        if time_window:
            cutoff_time = datetime.now() - time_window
            activities = [
                a for a in activities 
                if datetime.fromisoformat(a['timestamp']) >= cutoff_time
            ]
        
        # Get error activities
        error_activities = [a for a in activities if a['activity_type'] == 'error']
        
        if not error_activities:
            return {
                'total_errors': 0,
                'error_types': {},
                'error_rate': 0.0
            }
        
        # Analyze error types
        error_types = {}
        for error in error_activities:
            error_type = error['details'].get('error_type', 'unknown')
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        # Calculate error rate
        total_activities = len(activities)
        error_rate = len(error_activities) / max(total_activities, 1)
        
        return {
            'total_errors': len(error_activities),
            'error_types': error_types,
            'error_rate': error_rate,
            'most_common_error': max(error_types.items(), key=lambda x: x[1])[0] if error_types else None
        }
    
    def export_logs(self, 
                   log_type: str,
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   format: str = 'json') -> Optional[str]:
        """
        Export logs in specified format.
        
        Args:
            log_type: Type of logs to export ('activity', 'performance', 'errors', 'interactions')
            start_date: Optional start date filter
            end_date: Optional end date filter
            format: Export format ('json', 'csv')
            
        Returns:
            Exported logs as string or None if failed
        """
        try:
            # Determine log file
            log_files = {
                'activity': 'activity.log',
                'performance': 'performance.log',
                'errors': 'ui_errors.log',
                'interactions': 'user_interactions.log'
            }
            
            if log_type not in log_files:
                return None
            
            log_file = self.log_dir / log_files[log_type]
            
            if not log_file.exists():
                return None
            
            # Read and filter log entries
            log_entries = []
            
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        # Parse log line
                        parts = line.strip().split(' - ', 3)
                        if len(parts) >= 3:
                            timestamp_str = parts[0]
                            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                            
                            # Apply date filters
                            if start_date and timestamp < start_date:
                                continue
                            if end_date and timestamp > end_date:
                                continue
                            
                            # Try to parse JSON content
                            if len(parts) == 4:
                                try:
                                    json_content = json.loads(parts[3])
                                    log_entries.append({
                                        'timestamp': timestamp_str,
                                        'level': parts[1],
                                        'content': json_content
                                    })
                                except json.JSONDecodeError:
                                    log_entries.append({
                                        'timestamp': timestamp_str,
                                        'level': parts[1],
                                        'message': parts[3]
                                    })
                    except Exception:
                        continue
            
            # Export in requested format
            if format.lower() == 'json':
                return json.dumps(log_entries, indent=2, ensure_ascii=False)
            
            elif format.lower() == 'csv':
                if log_entries:
                    df = pd.json_normalize(log_entries)
                    return df.to_csv(index=False)
                else:
                    return "No log entries found"
            
            else:
                return None
                
        except Exception as e:
            print(f"Error exporting logs: {e}")
            return None
    
    def cleanup_old_logs(self, days_to_keep: int = 30) -> int:
        """
        Clean up old log entries.
        
        Args:
            days_to_keep: Number of days of logs to keep
            
        Returns:
            Number of log files cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cleaned_count = 0
        
        # Clean up rotated log files
        for log_file in self.log_dir.glob("*.log.*"):
            try:
                # Check file modification time
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_time < cutoff_date:
                    log_file.unlink()
                    cleaned_count += 1
            except Exception as e:
                print(f"Error cleaning up log file {log_file}: {e}")
        
        return cleaned_count