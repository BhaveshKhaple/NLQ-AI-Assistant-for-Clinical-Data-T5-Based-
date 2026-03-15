#!/usr/bin/env python3
"""
UI Error Handler
Comprehensive error handling and user-friendly error display for the Streamlit UI.
"""

import streamlit as st
import traceback
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
import json
import pandas as pd

class UIErrorHandler:
    """
    Comprehensive error handler for the Clinical NLQ Streamlit application.
    Provides user-friendly error messages, error recovery suggestions, and error logging.
    """
    
    def __init__(self, log_dir: str = "d:/projects/healthca/logs"):
        """
        Initialize the error handler.
        
        Args:
            log_dir: Directory for error logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup error logger
        self.logger = self._setup_error_logger()
        
        # Error message templates
        self.error_templates = {
            'SQL_GENERATION_ERROR': {
                'title': '🧠 SQL Generation Error',
                'message': 'The system had trouble converting your question to SQL.',
                'suggestions': [
                    'Try rephrasing your question more clearly',
                    'Be more specific about what data you want',
                    'Use simpler language and avoid complex nested questions',
                    'Check if you\'re asking about data that exists in our database'
                ],
                'severity': 'warning'
            },
            'DATABASE_ERROR': {
                'title': '💾 Database Error',
                'message': 'There was a problem executing the query against the database.',
                'suggestions': [
                    'The query might be too complex - try a simpler question',
                    'The requested data might not exist',
                    'There might be a temporary database connection issue',
                    'Try again in a few moments'
                ],
                'severity': 'error'
            },
            'TIMEOUT_ERROR': {
                'title': '⏱️ Query Timeout',
                'message': 'Your query took too long to process.',
                'suggestions': [
                    'Try asking for a smaller subset of data',
                    'Be more specific in your query to reduce processing time',
                    'Consider breaking complex questions into simpler parts',
                    'Try again - the system might be busy'
                ],
                'severity': 'warning'
            },
            'VALIDATION_ERROR': {
                'title': '✅ Validation Error',
                'message': 'The generated SQL query failed validation checks.',
                'suggestions': [
                    'Try rephrasing your question',
                    'Make sure you\'re asking about valid clinical data',
                    'Avoid using technical database terms',
                    'Use natural language to describe what you want'
                ],
                'severity': 'warning'
            },
            'PIPELINE_ERROR': {
                'title': '🔧 System Error',
                'message': 'There was an internal system error processing your request.',
                'suggestions': [
                    'Try refreshing the page',
                    'Check if the system is properly initialized',
                    'Try a different query to see if the issue persists',
                    'Contact support if the problem continues'
                ],
                'severity': 'error'
            },
            'CONNECTION_ERROR': {
                'title': '🔌 Connection Error',
                'message': 'Unable to connect to the database or model service.',
                'suggestions': [
                    'Check your internet connection',
                    'The service might be temporarily unavailable',
                    'Try refreshing the page',
                    'Contact support if the issue persists'
                ],
                'severity': 'error'
            },
            'AUTHENTICATION_ERROR': {
                'title': '🔐 Authentication Error',
                'message': 'There was a problem with user authentication.',
                'suggestions': [
                    'Try logging in again',
                    'Check your credentials',
                    'Clear your browser cache and cookies',
                    'Contact support if you continue having issues'
                ],
                'severity': 'error'
            },
            'RATE_LIMIT_ERROR': {
                'title': '🚦 Rate Limit Exceeded',
                'message': 'You\'ve made too many requests in a short time.',
                'suggestions': [
                    'Please wait a moment before trying again',
                    'Consider combining multiple questions into one',
                    'Space out your queries to avoid hitting limits',
                    'Contact support if you need higher limits'
                ],
                'severity': 'warning'
            }
        }
        
        # Error recovery strategies
        self.recovery_strategies = {
            'SQL_GENERATION_ERROR': self._suggest_query_improvements,
            'DATABASE_ERROR': self._suggest_database_alternatives,
            'TIMEOUT_ERROR': self._suggest_performance_improvements,
            'VALIDATION_ERROR': self._suggest_validation_fixes
        }
        
        # Error statistics
        self.error_stats = {
            'total_errors': 0,
            'errors_by_type': {},
            'errors_by_session': {},
            'recent_errors': []
        }
    
    def _setup_error_logger(self) -> logging.Logger:
        """Setup error logger with file handler."""
        logger = logging.getLogger('clinical_nlq_ui_errors')
        logger.setLevel(logging.ERROR)
        logger.handlers.clear()
        
        # File handler
        handler = logging.FileHandler(
            self.log_dir / 'ui_error_handler.log',
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def handle_error(self, 
                    error: str,
                    context: Dict[str, Any],
                    error_type: Optional[str] = None,
                    show_details: bool = False,
                    show_recovery: bool = True) -> None:
        """
        Handle and display an error with user-friendly messaging.
        
        Args:
            error: Error message or exception
            context: Error context information
            error_type: Type of error for categorization
            show_details: Whether to show technical details
            show_recovery: Whether to show recovery suggestions
        """
        # Determine error type if not provided
        if not error_type:
            error_type = self._classify_error(str(error))
        
        # Log the error
        self._log_error(error, context, error_type)
        
        # Update statistics
        self._update_error_stats(error_type, context)
        
        # Get error template
        template = self.error_templates.get(error_type, self._get_default_template())
        
        # Display error message
        self._display_error_message(template, str(error), context, show_details)
        
        # Show recovery suggestions
        if show_recovery:
            self._display_recovery_suggestions(error_type, template, context)
        
        # Show error reporting option
        self._display_error_reporting(error, context, error_type)
    
    def _classify_error(self, error_message: str) -> str:
        """
        Classify error based on error message content.
        
        Args:
            error_message: Error message to classify
            
        Returns:
            Error type classification
        """
        error_lower = error_message.lower()
        
        if any(keyword in error_lower for keyword in ['sql', 'generation', 'invalid sql']):
            return 'SQL_GENERATION_ERROR'
        elif any(keyword in error_lower for keyword in ['network', 'unreachable', 'connection failed']):
            return 'CONNECTION_ERROR'
        elif any(keyword in error_lower for keyword in ['database', 'connection', 'psycopg2']):
            return 'DATABASE_ERROR'
        elif any(keyword in error_lower for keyword in ['timeout', 'time out', 'too long']):
            return 'TIMEOUT_ERROR'
        elif any(keyword in error_lower for keyword in ['validation', 'invalid', 'schema']):
            return 'VALIDATION_ERROR'
        elif any(keyword in error_lower for keyword in ['pipeline', 'initialization', 'model']):
            return 'PIPELINE_ERROR'
        elif any(keyword in error_lower for keyword in ['auth', 'permission', 'unauthorized']):
            return 'AUTHENTICATION_ERROR'
        elif any(keyword in error_lower for keyword in ['rate limit', 'too many requests']):
            return 'RATE_LIMIT_ERROR'
        else:
            return 'UNKNOWN_ERROR'
    
    def _get_default_template(self) -> Dict[str, Any]:
        """Get default error template for unknown errors."""
        return {
            'title': '❌ Unexpected Error',
            'message': 'An unexpected error occurred while processing your request.',
            'suggestions': [
                'Try refreshing the page',
                'Try a different query',
                'Check if the issue persists',
                'Contact support if the problem continues'
            ],
            'severity': 'error'
        }
    
    def _log_error(self, error: str, context: Dict[str, Any], error_type: str) -> None:
        """Log error details."""
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'error_message': str(error),
            'context': context,
            'session_id': context.get('session_id', 'unknown'),
            'user_id': context.get('user_id', 'anonymous')
        }
        
        log_message = json.dumps(error_record, ensure_ascii=False)
        self.logger.error(log_message)
    
    def _update_error_stats(self, error_type: str, context: Dict[str, Any]) -> None:
        """Update error statistics."""
        self.error_stats['total_errors'] += 1
        
        # Update error type counts
        if error_type not in self.error_stats['errors_by_type']:
            self.error_stats['errors_by_type'][error_type] = 0
        self.error_stats['errors_by_type'][error_type] += 1
        
        # Update session error counts
        session_id = context.get('session_id', 'unknown')
        if session_id not in self.error_stats['errors_by_session']:
            self.error_stats['errors_by_session'][session_id] = 0
        self.error_stats['errors_by_session'][session_id] += 1
        
        # Add to recent errors (keep last 50)
        error_record = {
            'timestamp': datetime.now(),
            'error_type': error_type,
            'context': context
        }
        self.error_stats['recent_errors'].append(error_record)
        if len(self.error_stats['recent_errors']) > 50:
            self.error_stats['recent_errors'] = self.error_stats['recent_errors'][-50:]
    
    def _display_error_message(self, 
                              template: Dict[str, Any],
                              error_message: str,
                              context: Dict[str, Any],
                              show_details: bool) -> None:
        """Display the main error message."""
        severity = template.get('severity', 'error')
        
        if severity == 'error':
            st.error(f"{template['title']}: {template['message']}")
        elif severity == 'warning':
            st.warning(f"{template['title']}: {template['message']}")
        else:
            st.info(f"{template['title']}: {template['message']}")
        
        # Show technical details if requested
        if show_details:
            with st.expander("🔍 Technical Details"):
                st.text(f"Error Message: {error_message}")
                st.text(f"Error Type: {self._classify_error(error_message)}")
                
                if context:
                    st.text("Context:")
                    for key, value in context.items():
                        st.text(f"  {key}: {value}")
    
    def _display_recovery_suggestions(self, 
                                    error_type: str,
                                    template: Dict[str, Any],
                                    context: Dict[str, Any]) -> None:
        """Display recovery suggestions."""
        suggestions = template.get('suggestions', [])
        
        if suggestions:
            st.info("💡 **Suggestions to resolve this issue:**")
            for i, suggestion in enumerate(suggestions, 1):
                st.write(f"{i}. {suggestion}")
        
        # Show specific recovery strategies if available
        if error_type in self.recovery_strategies:
            recovery_func = self.recovery_strategies[error_type]
            recovery_suggestions = recovery_func(context)
            
            if recovery_suggestions:
                st.info("🔧 **Specific recommendations:**")
                for suggestion in recovery_suggestions:
                    st.write(f"• {suggestion}")
    
    def _display_error_reporting(self, 
                               error: str,
                               context: Dict[str, Any],
                               error_type: str) -> None:
        """Display error reporting options."""
        with st.expander("📝 Report this Error"):
            st.write("Help us improve by reporting this error:")
            
            col1, col2 = st.columns(2)
            
            import time
            unique_key_base = f"error_btn_{int(time.time()*1000)}_{hash(str(error))}"
            
            with col1:
                if st.button("📧 Report Error", help="Send error report to support", key=f"{unique_key_base}_report"):
                    self._create_error_report(error, context, error_type)
                    st.success("✅ Error report created!")
            
            with col2:
                if st.button("📋 Copy Error Details", help="Copy error details to clipboard", key=f"{unique_key_base}_copy"):
                    error_details = self._format_error_for_copy(error, context, error_type)
                    st.code(error_details, language='text')
                    st.info("📋 Error details displayed above - you can select and copy them")
    
    def _suggest_query_improvements(self, context: Dict[str, Any]) -> List[str]:
        """Suggest query improvements for SQL generation errors."""
        suggestions = []
        
        nlq = context.get('nlq', '')
        if nlq:
            if len(nlq) > 200:
                suggestions.append("Your question is quite long - try breaking it into smaller, simpler questions")
            
            if '?' not in nlq:
                suggestions.append("Try phrasing your input as a clear question ending with '?'")
            
            if any(word in nlq.lower() for word in ['and', 'or', 'but', 'however']):
                suggestions.append("Your question contains multiple parts - try asking one thing at a time")
            
            if any(word in nlq.lower() for word in ['sql', 'select', 'from', 'where']):
                suggestions.append("Avoid using SQL keywords - describe what you want in natural language")
        
        return suggestions
    
    def _suggest_database_alternatives(self, context: Dict[str, Any]) -> List[str]:
        """Suggest alternatives for database errors."""
        suggestions = []
        
        generated_sql = context.get('generated_sql', '')
        if generated_sql:
            if 'JOIN' in generated_sql.upper():
                suggestions.append("Try asking about one table at a time instead of combining multiple data sources")
            
            if 'GROUP BY' in generated_sql.upper():
                suggestions.append("Try asking for individual records first, then ask for summaries")
            
            if len(generated_sql) > 500:
                suggestions.append("The generated query is complex - try asking a simpler question")
        
        return suggestions
    
    def _suggest_performance_improvements(self, context: Dict[str, Any]) -> List[str]:
        """Suggest performance improvements for timeout errors."""
        suggestions = [
            "Add date ranges to limit the data (e.g., 'patients from last month')",
            "Ask for a specific number of results (e.g., 'show me 10 patients')",
            "Be more specific about the data you need",
            "Try asking about a subset of the data first"
        ]
        
        return suggestions
    
    def _suggest_validation_fixes(self, context: Dict[str, Any]) -> List[str]:
        """Suggest fixes for validation errors."""
        suggestions = [
            "Make sure you're asking about clinical data that exists in our system",
            "Use standard medical terminology",
            "Avoid abbreviations that might be ambiguous",
            "Be specific about what type of data you want (patients, diagnoses, medications, etc.)"
        ]
        
        return suggestions
    
    def _create_error_report(self, 
                           error: str,
                           context: Dict[str, Any],
                           error_type: str) -> None:
        """Create an error report file."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'error_message': str(error),
            'context': context,
            'user_session': {
                'session_id': context.get('session_id', 'unknown'),
                'user_id': context.get('user_id', 'anonymous')
            },
            'system_info': {
                'streamlit_version': st.__version__,
                'error_handler_version': '1.0.0'
            }
        }
        
        # Save report to file
        report_file = self.log_dir / f"error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
        except Exception as e:
            st.error(f"Failed to create error report: {e}")
    
    def _format_error_for_copy(self, 
                              error: str,
                              context: Dict[str, Any],
                              error_type: str) -> str:
        """Format error details for copying."""
        lines = [
            "=== ERROR REPORT ===",
            f"Timestamp: {datetime.now().isoformat()}",
            f"Error Type: {error_type}",
            f"Error Message: {error}",
            "",
            "Context:",
        ]
        
        for key, value in context.items():
            lines.append(f"  {key}: {value}")
        
        lines.extend([
            "",
            "Session Info:",
            f"  Session ID: {context.get('session_id', 'unknown')}",
            f"  User ID: {context.get('user_id', 'anonymous')}",
            "",
            "=== END REPORT ==="
        ])
        
        return "\n".join(lines)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics summary."""
        return {
            'total_errors': self.error_stats['total_errors'],
            'errors_by_type': dict(self.error_stats['errors_by_type']),
            'most_common_error': max(
                self.error_stats['errors_by_type'].items(),
                key=lambda x: x[1]
            )[0] if self.error_stats['errors_by_type'] else None,
            'recent_error_count': len(self.error_stats['recent_errors']),
            'sessions_with_errors': len(self.error_stats['errors_by_session'])
        }
    
    def render_error_dashboard(self) -> None:
        """Render error statistics dashboard."""
        st.subheader("🚨 Error Dashboard")
        
        stats = self.get_error_statistics()
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Errors", stats['total_errors'])
        
        with col2:
            st.metric("Error Types", len(stats['errors_by_type']))
        
        with col3:
            st.metric("Recent Errors", stats['recent_error_count'])
        
        with col4:
            st.metric("Affected Sessions", stats['sessions_with_errors'])
        
        # Error breakdown
        if stats['errors_by_type']:
            st.subheader("📊 Error Breakdown")
            
            # Create pie chart
            import plotly.express as px
            
            fig = px.pie(
                values=list(stats['errors_by_type'].values()),
                names=list(stats['errors_by_type'].keys()),
                title="Errors by Type"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Error types table
            error_df = pd.DataFrame([
                {
                    'Error Type': error_type,
                    'Count': count,
                    'Percentage': f"{count/stats['total_errors']:.1%}"
                }
                for error_type, count in stats['errors_by_type'].items()
            ])
            
            st.dataframe(error_df, use_container_width=True)
        
        # Recent errors
        if self.error_stats['recent_errors']:
            st.subheader("🕒 Recent Errors")
            
            recent_df = pd.DataFrame([
                {
                    'Timestamp': error['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                    'Error Type': error['error_type'],
                    'Session ID': error['context'].get('session_id', 'unknown')[:8] + '...',
                    'Component': error['context'].get('component', 'unknown')
                }
                for error in self.error_stats['recent_errors'][-10:]
            ])
            
            st.dataframe(recent_df, use_container_width=True)
    
    def clear_error_stats(self) -> None:
        """Clear error statistics."""
        self.error_stats = {
            'total_errors': 0,
            'errors_by_type': {},
            'errors_by_session': {},
            'recent_errors': []
        }
        
        st.success("✅ Error statistics cleared!")
    
    def export_error_logs(self, format: str = 'json') -> Optional[str]:
        """
        Export error logs in specified format.
        
        Args:
            format: Export format ('json', 'csv')
            
        Returns:
            Exported data as string or None if failed
        """
        try:
            if format.lower() == 'json':
                return json.dumps(self.error_stats, indent=2, ensure_ascii=False, default=str)
            
            elif format.lower() == 'csv':
                import pandas as pd
                
                if self.error_stats['recent_errors']:
                    df = pd.DataFrame([
                        {
                            'timestamp': error['timestamp'],
                            'error_type': error['error_type'],
                            'session_id': error['context'].get('session_id', 'unknown'),
                            'component': error['context'].get('component', 'unknown'),
                            'nlq': error['context'].get('nlq', '')[:100]
                        }
                        for error in self.error_stats['recent_errors']
                    ])
                    
                    return df.to_csv(index=False)
                else:
                    return "No error data available"
            
            else:
                return None
                
        except Exception as e:
            st.error(f"Failed to export error logs: {e}")
            return None