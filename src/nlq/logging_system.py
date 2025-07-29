#!/usr/bin/env python3
"""
Logging System
Comprehensive logging for debugging, auditing, and monitoring the inference pipeline.
"""

import os
import logging
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import yaml
from logging.handlers import RotatingFileHandler
import traceback

class InferenceLogger:
    """
    Comprehensive logging system for the clinical NLQ inference pipeline.
    Handles query logging, error tracking, performance monitoring, and audit trails.
    """
    
    def __init__(self, config_path: str = "d:/projects/healthca/config/config.yaml"):
        """
        Initialize the logging system.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.log_dir = Path("d:/projects/healthca/logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Initialize loggers
        self.main_logger = self._setup_main_logger()
        self.audit_logger = self._setup_audit_logger()
        self.performance_logger = self._setup_performance_logger()
        self.error_logger = self._setup_error_logger()
        
        # Session tracking
        self.session_id = f"session_{int(time.time() * 1000)}"
        self.session_start = datetime.now()
        
        # Statistics tracking
        self.stats = {
            'queries_logged': 0,
            'errors_logged': 0,
            'performance_entries': 0,
            'audit_entries': 0,
            'session_start': self.session_start.isoformat(),
            'session_id': self.session_id
        }
        
        self.main_logger.info(f"🔧 Inference Logger initialized - Session: {self.session_id}")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"❌ Failed to load config: {e}")
            # Return default config
            return {
                'logging': {
                    'level': 'INFO',
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    'file': './logs/nlq_assistant.log',
                    'max_bytes': 10485760,
                    'backup_count': 5,
                    'audit_file': './logs/audit.log'
                }
            }
    
    def _setup_main_logger(self) -> logging.Logger:
        """Setup main application logger."""
        logger = logging.getLogger('clinical_nlq_main')
        logger.setLevel(getattr(logging, self.config.get('logging', {}).get('level', 'INFO')))
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # File handler with rotation
        log_file = self.log_dir / "nlq_assistant.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=self.config.get('logging', {}).get('max_bytes', 10485760),
            backupCount=self.config.get('logging', {}).get('backup_count', 5),
            encoding='utf-8'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        
        # Formatter
        formatter = logging.Formatter(
            self.config.get('logging', {}).get('format', 
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _setup_audit_logger(self) -> logging.Logger:
        """Setup audit logger for security and compliance."""
        logger = logging.getLogger('clinical_nlq_audit')
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        
        # Audit file handler
        audit_file = self.log_dir / "audit.log"
        file_handler = RotatingFileHandler(
            audit_file,
            maxBytes=self.config.get('logging', {}).get('max_bytes', 10485760),
            backupCount=self.config.get('logging', {}).get('backup_count', 5),
            encoding='utf-8'
        )
        
        # JSON formatter for structured audit logs
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def _setup_performance_logger(self) -> logging.Logger:
        """Setup performance logger for monitoring."""
        logger = logging.getLogger('clinical_nlq_performance')
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        
        # Performance file handler
        perf_file = self.log_dir / "performance.log"
        file_handler = RotatingFileHandler(
            perf_file,
            maxBytes=self.config.get('logging', {}).get('max_bytes', 10485760),
            backupCount=self.config.get('logging', {}).get('backup_count', 5),
            encoding='utf-8'
        )
        
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def _setup_error_logger(self) -> logging.Logger:
        """Setup dedicated error logger."""
        logger = logging.getLogger('clinical_nlq_errors')
        logger.setLevel(logging.ERROR)
        logger.handlers.clear()
        
        # Error file handler
        error_file = self.log_dir / "errors.log"
        file_handler = RotatingFileHandler(
            error_file,
            maxBytes=self.config.get('logging', {}).get('max_bytes', 10485760),
            backupCount=self.config.get('logging', {}).get('backup_count', 5),
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s\n%(pathname)s:%(lineno)d\n'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def log_query_start(self, 
                       nlq: str, 
                       user_id: Optional[str] = None,
                       session_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Log the start of a query processing.
        
        Args:
            nlq: Natural language query
            user_id: User identifier
            session_info: Additional session information
            
        Returns:
            Query ID for tracking
        """
        query_id = f"query_{int(time.time() * 1000)}_{self.stats['queries_logged']}"
        
        log_entry = {
            'event': 'query_start',
            'query_id': query_id,
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'nlq': nlq,
            'nlq_length': len(nlq),
            'user_id': user_id,
            'session_info': session_info or {}
        }
        
        self.main_logger.info(f"🚀 Query started: {query_id} - {nlq[:100]}...")
        self.audit_logger.info(json.dumps(log_entry))
        
        self.stats['queries_logged'] += 1
        self.stats['audit_entries'] += 1
        
        return query_id
    
    def log_sql_generation(self, 
                          query_id: str,
                          generation_result: Dict[str, Any]):
        """
        Log SQL generation results.
        
        Args:
            query_id: Query identifier
            generation_result: Result from inference engine
        """
        log_entry = {
            'event': 'sql_generation',
            'query_id': query_id,
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'generated_sql': generation_result.get('generated_sql', ''),
            'generation_time': generation_result.get('generation_time', 0),
            'validation': generation_result.get('validation', {}),
            'metadata': generation_result.get('metadata', {}),
            'success': generation_result.get('validation', {}).get('is_valid', False)
        }
        
        if log_entry['success']:
            self.main_logger.info(f"✅ SQL generated for {query_id} in {log_entry['generation_time']:.3f}s")
        else:
            self.main_logger.warning(f"⚠️ SQL generation issues for {query_id}")
            
        self.audit_logger.info(json.dumps(log_entry))
        self.stats['audit_entries'] += 1
    
    def log_database_execution(self, 
                              query_id: str,
                              execution_result: Dict[str, Any]):
        """
        Log database execution results.
        
        Args:
            query_id: Query identifier
            execution_result: Result from database executor
        """
        log_entry = {
            'event': 'database_execution',
            'query_id': query_id,
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'success': execution_result.get('success', False),
            'execution_time': execution_result.get('execution_time', 0),
            'rows_returned': execution_result.get('rows_returned', 0),
            'error_type': execution_result.get('error_type'),
            'security_check': execution_result.get('security_check', {}),
            'truncated': execution_result.get('truncated', False)
        }
        
        # Don't log actual SQL or data for security
        if not log_entry['success']:
            log_entry['error'] = execution_result.get('error', '')
        
        if log_entry['success']:
            self.main_logger.info(
                f"✅ Query {query_id} executed successfully: "
                f"{log_entry['rows_returned']} rows in {log_entry['execution_time']:.3f}s"
            )
        else:
            self.main_logger.error(
                f"❌ Query {query_id} execution failed: {log_entry.get('error', 'Unknown error')}"
            )
            
        self.audit_logger.info(json.dumps(log_entry))
        self.stats['audit_entries'] += 1
    
    def log_result_formatting(self, 
                             query_id: str,
                             format_results: Dict[str, Any]):
        """
        Log result formatting.
        
        Args:
            query_id: Query identifier
            format_results: Results from result formatter
        """
        log_entry = {
            'event': 'result_formatting',
            'query_id': query_id,
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'formats_requested': list(format_results.get('formats', {}).keys()),
            'success': format_results.get('success', False),
            'formatting_errors': []
        }
        
        # Check for formatting errors
        for format_type, result in format_results.get('formats', {}).items():
            if not result.get('success', False):
                log_entry['formatting_errors'].append({
                    'format': format_type,
                    'error': result.get('error', 'Unknown error')
                })
        
        if log_entry['success']:
            self.main_logger.info(f"✅ Results formatted for {query_id}: {log_entry['formats_requested']}")
        else:
            self.main_logger.warning(f"⚠️ Formatting issues for {query_id}")
            
        self.audit_logger.info(json.dumps(log_entry))
        self.stats['audit_entries'] += 1
    
    def log_query_complete(self, 
                          query_id: str,
                          total_time: float,
                          success: bool,
                          final_result: Optional[Dict[str, Any]] = None):
        """
        Log query completion.
        
        Args:
            query_id: Query identifier
            total_time: Total processing time
            success: Whether query was successful
            final_result: Final result summary
        """
        log_entry = {
            'event': 'query_complete',
            'query_id': query_id,
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'total_time': total_time,
            'success': success,
            'result_summary': {
                'rows_returned': final_result.get('rows_returned', 0) if final_result else 0,
                'formats_generated': list(final_result.get('formats', {}).keys()) if final_result else []
            }
        }
        
        if success:
            self.main_logger.info(f"🎉 Query {query_id} completed successfully in {total_time:.3f}s")
        else:
            self.main_logger.error(f"💥 Query {query_id} failed after {total_time:.3f}s")
            
        self.audit_logger.info(json.dumps(log_entry))
        self.stats['audit_entries'] += 1
    
    def log_error(self, 
                  error: Exception,
                  context: Dict[str, Any],
                  query_id: Optional[str] = None):
        """
        Log errors with full context and stack trace.
        
        Args:
            error: Exception object
            context: Error context information
            query_id: Associated query ID if applicable
        """
        error_entry = {
            'event': 'error',
            'query_id': query_id,
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'stack_trace': traceback.format_exc()
        }
        
        self.error_logger.error(json.dumps(error_entry, indent=2))
        self.main_logger.error(f"❌ Error in {context.get('component', 'unknown')}: {str(error)}")
        
        self.stats['errors_logged'] += 1
    
    def log_performance_metrics(self, 
                               component: str,
                               metrics: Dict[str, Any],
                               query_id: Optional[str] = None):
        """
        Log performance metrics.
        
        Args:
            component: Component name (inference_engine, database_executor, etc.)
            metrics: Performance metrics
            query_id: Associated query ID if applicable
        """
        perf_entry = {
            'event': 'performance_metrics',
            'component': component,
            'query_id': query_id,
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics
        }
        
        self.performance_logger.info(json.dumps(perf_entry))
        self.stats['performance_entries'] += 1
        
        # Log key metrics to main logger
        if 'execution_time' in metrics:
            self.main_logger.info(f"⚡ {component} performance: {metrics['execution_time']:.3f}s")
    
    def log_security_event(self, 
                          event_type: str,
                          details: Dict[str, Any],
                          severity: str = 'INFO',
                          query_id: Optional[str] = None):
        """
        Log security-related events.
        
        Args:
            event_type: Type of security event
            details: Event details
            severity: Event severity (INFO, WARNING, ERROR, CRITICAL)
            query_id: Associated query ID if applicable
        """
        security_entry = {
            'event': 'security_event',
            'event_type': event_type,
            'severity': severity,
            'query_id': query_id,
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        
        self.audit_logger.info(json.dumps(security_entry))
        
        # Log to main logger based on severity
        log_method = getattr(self.main_logger, severity.lower(), self.main_logger.info)
        log_method(f"🔒 Security event ({event_type}): {details.get('message', 'No message')}")
        
        self.stats['audit_entries'] += 1
    
    def log_system_info(self, system_info: Dict[str, Any]):
        """
        Log system information and configuration.
        
        Args:
            system_info: System information dictionary
        """
        info_entry = {
            'event': 'system_info',
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'system_info': system_info
        }
        
        self.audit_logger.info(json.dumps(info_entry))
        self.main_logger.info("📊 System information logged")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics."""
        current_time = datetime.now()
        session_duration = (current_time - self.session_start).total_seconds()
        
        return {
            **self.stats,
            'session_duration_seconds': session_duration,
            'current_timestamp': current_time.isoformat(),
            'queries_per_minute': self.stats['queries_logged'] / max(session_duration / 60, 1),
            'errors_per_query': self.stats['errors_logged'] / max(self.stats['queries_logged'], 1)
        }
    
    def export_logs(self, 
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   log_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Export logs for analysis or archival.
        
        Args:
            start_time: Start time for log export
            end_time: End time for log export
            log_types: Types of logs to export ('main', 'audit', 'performance', 'error')
            
        Returns:
            Dict with exported log data
        """
        log_types = log_types or ['main', 'audit', 'performance', 'error']
        exported_logs = {}
        
        log_files = {
            'main': self.log_dir / "nlq_assistant.log",
            'audit': self.log_dir / "audit.log",
            'performance': self.log_dir / "performance.log",
            'error': self.log_dir / "errors.log"
        }
        
        for log_type in log_types:
            if log_type in log_files:
                log_file = log_files[log_type]
                if log_file.exists():
                    try:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            exported_logs[log_type] = f.read()
                    except Exception as e:
                        self.main_logger.error(f"Failed to export {log_type} logs: {e}")
                        exported_logs[log_type] = f"Error reading log file: {e}"
        
        return {
            'export_timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'log_types': log_types,
            'logs': exported_logs,
            'stats': self.get_session_stats()
        }
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """
        Clean up old log files.
        
        Args:
            days_to_keep: Number of days of logs to keep
        """
        try:
            import glob
            from datetime import timedelta
            
            cutoff_time = datetime.now() - timedelta(days=days_to_keep)
            
            # Find old log files
            log_patterns = [
                self.log_dir / "*.log.*",  # Rotated log files
                self.log_dir / "*.log.old"
            ]
            
            deleted_count = 0
            for pattern in log_patterns:
                for log_file in glob.glob(str(pattern)):
                    file_path = Path(log_file)
                    if file_path.stat().st_mtime < cutoff_time.timestamp():
                        file_path.unlink()
                        deleted_count += 1
            
            self.main_logger.info(f"🧹 Cleaned up {deleted_count} old log files")
            
        except Exception as e:
            self.main_logger.error(f"❌ Error cleaning up logs: {e}")
    
    def close(self):
        """Close all loggers and handlers."""
        for logger in [self.main_logger, self.audit_logger, self.performance_logger, self.error_logger]:
            for handler in logger.handlers:
                handler.close()
        
        self.main_logger.info(f"🔚 Logging session {self.session_id} closed")


# Global logger instance
_global_logger = None

def get_logger() -> InferenceLogger:
    """Get global logger instance."""
    global _global_logger
    if _global_logger is None:
        _global_logger = InferenceLogger()
    return _global_logger

def reset_logger():
    """Reset global logger instance."""
    global _global_logger
    if _global_logger:
        _global_logger.close()
    _global_logger = None