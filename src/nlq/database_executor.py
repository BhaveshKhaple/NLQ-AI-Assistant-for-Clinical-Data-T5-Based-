#!/usr/bin/env python3
"""
Database Executor
Securely executes generated SQL queries against PostgreSQL database with comprehensive error handling.
"""

import os
import logging
import time
import re
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import yaml
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseExecutor:
    """
    Secure database executor for running generated SQL queries.
    Provides connection management, query validation, and comprehensive error handling.
    """
    
    def __init__(self, config_path: str = "d:/projects/healthca/config/config.yaml"):
        """
        Initialize the database executor.
        
        Args:
            config_path: Path to configuration file
        """
        # Load environment variables from .env file
        self._load_env_file()
        self.config = self._load_config(config_path)
        self.engine = None
        self.Session = None
        self.metadata = None
        
        # Query execution statistics
        self.execution_stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'total_execution_time': 0.0,
            'avg_execution_time': 0.0,
            'queries_by_type': {},
            'error_counts': {}
        }
        
        # Security settings
        self.max_query_timeout = self.config.get('performance', {}).get('query_timeout', 30)
        self.max_result_rows = self.config.get('performance', {}).get('max_export_rows', 10000)
        
        # Allowed SQL operations (whitelist approach)
        self.allowed_operations = {'SELECT', 'WITH'}  # Only read operations
        
        logger.info("🔧 Database Executor initialized")
    
    def _load_env_file(self):
        """Load environment variables from .env file"""
        try:
            from pathlib import Path
            
            # Find .env file in project root
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent  # Go up from src/nlq to project root
            env_path = project_root / '.env'
            
            if not env_path.exists():
                logger.warning(f"⚠️ .env file not found at {env_path}")
                return
            
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse key=value pairs
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        # Set environment variable
                        os.environ[key] = value
            
            logger.info("✅ Environment variables loaded from .env file")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to load .env file: {e}")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file with environment variable substitution."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_content = f.read()
            
            # Substitute environment variables
            config_content = self._substitute_env_vars(config_content)
            
            config = yaml.safe_load(config_content)
            logger.info(f"✅ Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            # Return default config with environment variables
            return {
                'database': {
                    'host': os.getenv('DB_HOST', 'localhost'),
                    'port': int(os.getenv('DB_PORT', 5432)),
                    'name': os.getenv('DB_NAME', 'medical'),
                    'username': os.getenv('DB_USERNAME', 'postgres'),
                    'schema': os.getenv('DB_SCHEMA', 'clinical_data')
                },
                'performance': {
                    'query_timeout': 30,
                    'max_export_rows': 10000
                }
            }
    
    def _substitute_env_vars(self, content: str) -> str:
        """Substitute environment variables in config content."""
        import re
        
        def replace_env_var(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))  # Return original if env var not found
        
        # Replace ${VAR_NAME} patterns
        return re.sub(r'\$\{([^}]+)\}', replace_env_var, content)
    
    def connect(self) -> bool:
        """
        Establish database connection using SQLAlchemy.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            db_config = self.config.get('database', {})
            
            # Get database credentials from environment variables or config
            host = db_config.get('host', os.getenv('DB_HOST', 'localhost'))
            port = db_config.get('port', int(os.getenv('DB_PORT', 5432)))
            database = db_config.get('name', os.getenv('DB_NAME', 'medical'))
            username = db_config.get('username', os.getenv('DB_USERNAME', 'postgres'))
            password = os.getenv('DB_PASSWORD', '')
            
            if not password:
                logger.warning("⚠️ DB_PASSWORD environment variable not set")
            
            # Build connection string with URL encoding for password
            from urllib.parse import quote_plus
            encoded_password = quote_plus(password)
            
            connection_string = (
                f"postgresql://{username}:{encoded_password}@{host}:{port}/{database}"
            )
            
            # Create engine with connection pooling
            self.engine = create_engine(
                connection_string,
                pool_size=db_config.get('pool_size', 10),
                max_overflow=db_config.get('max_overflow', 20),
                echo=db_config.get('echo', False),
                pool_pre_ping=True,  # Verify connections before use
                pool_recycle=3600,   # Recycle connections every hour
                connect_args={
                    'connect_timeout': 10,
                    'application_name': 'clinical_nlq_assistant'
                }
            )
            
            # Create session factory
            self.Session = sessionmaker(bind=self.engine)
            
            # Load metadata
            self.metadata = MetaData()
            self.metadata.reflect(bind=self.engine, schema=db_config.get('schema', 'clinical_data'))
            
            # Test connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            
            logger.info("✅ Database connection established successfully")
            logger.info(f"📊 Available tables: {list(self.metadata.tables.keys())}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            return False
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        Ensures proper connection cleanup.
        """
        if not self.engine:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        connection = self.engine.connect()
        try:
            yield connection
        finally:
            connection.close()
    
    def validate_sql_security(self, sql: str) -> Dict[str, Any]:
        """
        Validate SQL query for security and safety.
        
        Args:
            sql: SQL query to validate
            
        Returns:
            Dict with validation results
        """
        errors = []
        warnings = []
        
        # Normalize SQL for analysis
        sql_upper = sql.upper().strip()
        
        # Check for allowed operations only
        first_word = sql_upper.split()[0] if sql_upper.split() else ''
        if first_word not in self.allowed_operations:
            errors.append(f"Operation '{first_word}' not allowed. Only SELECT and WITH are permitted.")
        
        # Check for dangerous patterns
        dangerous_patterns = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE',
            'EXEC', 'EXECUTE', 'CALL', 'DECLARE', 'GRANT', 'REVOKE',
            'SHUTDOWN', 'BACKUP', 'RESTORE', 'BULK', 'OPENROWSET',
            'xp_', 'sp_', '--', '/*', '*/', ';--', 'UNION ALL SELECT'
        ]
        
        for pattern in dangerous_patterns:
            if pattern in sql_upper:
                errors.append(f"Dangerous pattern detected: '{pattern}'")
        
        # Check for schema compliance
        if 'clinical_data.' not in sql:
            warnings.append("Query should use 'clinical_data.' schema prefix")
        
        # Check for potential injection patterns
        injection_patterns = [
            r"'\s*OR\s*'1'\s*=\s*'1'",
            r"'\s*OR\s*1\s*=\s*1",
            r"UNION\s+SELECT",
            r";\s*DROP",
            r";\s*DELETE",
            r";\s*UPDATE"
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, sql_upper):
                errors.append(f"Potential SQL injection pattern detected")
                break
        
        # Check query complexity (prevent resource exhaustion)
        if sql.count('JOIN') > 5:
            warnings.append("Query has many JOINs, may be slow")
        
        if sql.count('SELECT') > 3:
            warnings.append("Query has multiple SELECT statements")
        
        is_safe = len(errors) == 0
        
        return {
            'is_safe': is_safe,
            'errors': errors,
            'warnings': warnings,
            'operation': first_word,
            'complexity_score': len(sql.split())
        }
    
    def execute_query(self, 
                     sql: str, 
                     timeout: Optional[int] = None,
                     max_rows: Optional[int] = None,
                     dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute SQL query with comprehensive error handling and security validation.
        
        Args:
            sql: SQL query to execute
            timeout: Query timeout in seconds
            max_rows: Maximum number of rows to return
            dry_run: If True, only validate query without executing
            
        Returns:
            Dict containing query results and metadata
        """
        start_time = time.time()
        query_id = f"query_{int(time.time() * 1000)}"
        
        try:
            # Update statistics
            self.execution_stats['total_queries'] += 1
            
            # Security validation
            security_check = self.validate_sql_security(sql)
            if not security_check['is_safe']:
                self.execution_stats['failed_queries'] += 1
                error_msg = f"Security validation failed: {'; '.join(security_check['errors'])}"
                logger.error(f"🚨 {error_msg}")
                
                return {
                    'query_id': query_id,
                    'sql': sql,
                    'success': False,
                    'error': error_msg,
                    'error_type': 'SECURITY_VIOLATION',
                    'execution_time': time.time() - start_time,
                    'security_check': security_check,
                    'rows_returned': 0,
                    'columns': []
                }
            
            # Log warnings
            if security_check['warnings']:
                for warning in security_check['warnings']:
                    logger.warning(f"⚠️ {warning}")
            
            # If dry run, return validation results only
            if dry_run:
                return {
                    'query_id': query_id,
                    'sql': sql,
                    'success': True,
                    'dry_run': True,
                    'security_check': security_check,
                    'execution_time': time.time() - start_time,
                    'message': 'Query validation successful (dry run)'
                }
            
            # Set execution parameters
            timeout = timeout or self.max_query_timeout
            max_rows = max_rows or self.max_result_rows
            
            # Execute query
            with self.get_connection() as conn:
                # Set query timeout
                conn.execute(text(f"SET statement_timeout = '{timeout}s'"))
                
                # Execute the main query
                result = conn.execute(text(sql))
                
                # Fetch results with row limit
                rows = result.fetchmany(max_rows + 1)  # Fetch one extra to check if limit exceeded
                
                # Check if result was truncated
                truncated = len(rows) > max_rows
                if truncated:
                    rows = rows[:max_rows]
                    logger.warning(f"⚠️ Results truncated to {max_rows} rows")
                
                # Get column information
                columns = [
                    {
                        'name': col.name,
                        'type': str(col.type),
                        'nullable': col.nullable if hasattr(col, 'nullable') else True
                    }
                    for col in result.cursor.description
                ] if result.cursor.description else []
                
                # Convert rows to list of dictionaries
                data = []
                if rows and result.cursor.description:
                    column_names = [desc[0] for desc in result.cursor.description]
                    data = [dict(zip(column_names, row)) for row in rows]
                
                execution_time = time.time() - start_time
                
                # Update statistics
                self.execution_stats['successful_queries'] += 1
                self.execution_stats['total_execution_time'] += execution_time
                self.execution_stats['avg_execution_time'] = (
                    self.execution_stats['total_execution_time'] / 
                    self.execution_stats['total_queries']
                )
                
                # Track query types
                query_type = security_check['operation']
                self.execution_stats['queries_by_type'][query_type] = (
                    self.execution_stats['queries_by_type'].get(query_type, 0) + 1
                )
                
                logger.info(f"✅ Query executed successfully in {execution_time:.3f}s, returned {len(data)} rows")
                
                return {
                    'query_id': query_id,
                    'sql': sql,
                    'success': True,
                    'data': data,
                    'columns': columns,
                    'rows_returned': len(data),
                    'execution_time': execution_time,
                    'truncated': truncated,
                    'security_check': security_check,
                    'metadata': {
                        'query_type': query_type,
                        'timestamp': datetime.now().isoformat(),
                        'timeout_used': timeout,
                        'max_rows_limit': max_rows
                    }
                }
                
        except psycopg2.OperationalError as e:
            # Database connection or operational errors
            execution_time = time.time() - start_time
            self.execution_stats['failed_queries'] += 1
            error_type = 'DATABASE_ERROR'
            
            if 'timeout' in str(e).lower():
                error_type = 'TIMEOUT_ERROR'
                logger.error(f"⏰ Query timeout after {timeout}s: {sql[:100]}...")
            else:
                logger.error(f"🔌 Database operational error: {e}")
            
            self.execution_stats['error_counts'][error_type] = (
                self.execution_stats['error_counts'].get(error_type, 0) + 1
            )
            
            return {
                'query_id': query_id,
                'sql': sql,
                'success': False,
                'error': str(e),
                'error_type': error_type,
                'execution_time': execution_time,
                'rows_returned': 0,
                'columns': []
            }
            
        except psycopg2.ProgrammingError as e:
            # SQL syntax or programming errors
            execution_time = time.time() - start_time
            self.execution_stats['failed_queries'] += 1
            error_type = 'SQL_SYNTAX_ERROR'
            
            logger.error(f"📝 SQL syntax error: {e}")
            
            self.execution_stats['error_counts'][error_type] = (
                self.execution_stats['error_counts'].get(error_type, 0) + 1
            )
            
            return {
                'query_id': query_id,
                'sql': sql,
                'success': False,
                'error': str(e),
                'error_type': error_type,
                'execution_time': execution_time,
                'rows_returned': 0,
                'columns': []
            }
            
        except Exception as e:
            # General errors
            execution_time = time.time() - start_time
            self.execution_stats['failed_queries'] += 1
            error_type = 'GENERAL_ERROR'
            
            logger.error(f"❌ Unexpected error executing query: {e}")
            
            self.execution_stats['error_counts'][error_type] = (
                self.execution_stats['error_counts'].get(error_type, 0) + 1
            )
            
            return {
                'query_id': query_id,
                'sql': sql,
                'success': False,
                'error': str(e),
                'error_type': error_type,
                'execution_time': execution_time,
                'rows_returned': 0,
                'columns': []
            }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test database connection and return system information.
        
        Returns:
            Dict with connection test results
        """
        try:
            with self.get_connection() as conn:
                # Test basic connectivity
                result = conn.execute(text("SELECT 1 as test"))
                test_result = result.fetchone()
                
                # Get database version
                version_result = conn.execute(text("SELECT version()"))
                db_version = version_result.fetchone()[0]
                
                # Get current schema
                schema_result = conn.execute(text("SELECT current_schema()"))
                current_schema = schema_result.fetchone()[0]
                
                # Get table count in clinical_data schema
                table_count_result = conn.execute(text("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = 'clinical_data'
                """))
                table_count = table_count_result.fetchone()[0]
                
                return {
                    'success': True,
                    'database_version': db_version,
                    'current_schema': current_schema,
                    'clinical_tables_count': table_count,
                    'available_tables': list(self.metadata.tables.keys()),
                    'connection_pool_size': self.engine.pool.size(),
                    'test_query_result': test_result[0] if test_result else None
                }
                
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_schema_info(self) -> Dict[str, Any]:
        """
        Get detailed schema information for the clinical database.
        
        Returns:
            Dict with schema information
        """
        try:
            schema_info = {
                'tables': {},
                'total_tables': 0,
                'total_columns': 0
            }
            
            with self.get_connection() as conn:
                # Get detailed table information
                table_info_query = text("""
                    SELECT 
                        t.table_name,
                        t.table_type,
                        c.column_name,
                        c.data_type,
                        c.is_nullable,
                        c.column_default
                    FROM information_schema.tables t
                    LEFT JOIN information_schema.columns c ON t.table_name = c.table_name
                    WHERE t.table_schema = 'clinical_data'
                    ORDER BY t.table_name, c.ordinal_position
                """)
                
                result = conn.execute(table_info_query)
                rows = result.fetchall()
                
                current_table = None
                for row in rows:
                    table_name = row[0]
                    
                    if table_name != current_table:
                        current_table = table_name
                        schema_info['tables'][table_name] = {
                            'table_type': row[1],
                            'columns': []
                        }
                        schema_info['total_tables'] += 1
                    
                    if row[2]:  # column_name exists
                        schema_info['tables'][table_name]['columns'].append({
                            'name': row[2],
                            'type': row[3],
                            'nullable': row[4] == 'YES',
                            'default': row[5]
                        })
                        schema_info['total_columns'] += 1
                
                return schema_info
                
        except Exception as e:
            logger.error(f"❌ Failed to get schema info: {e}")
            return {'error': str(e)}
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get database execution statistics."""
        return {
            **self.execution_stats.copy(),
            'success_rate': (
                self.execution_stats['successful_queries'] / 
                max(self.execution_stats['total_queries'], 1)
            ),
            'failure_rate': (
                self.execution_stats['failed_queries'] / 
                max(self.execution_stats['total_queries'], 1)
            )
        }
    
    def reset_stats(self):
        """Reset execution statistics."""
        self.execution_stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'total_execution_time': 0.0,
            'avg_execution_time': 0.0,
            'queries_by_type': {},
            'error_counts': {}
        }
        logger.info("📊 Execution statistics reset")
    
    def close(self):
        """Close database connections and cleanup resources."""
        if self.engine:
            self.engine.dispose()
            logger.info("🔌 Database connections closed")