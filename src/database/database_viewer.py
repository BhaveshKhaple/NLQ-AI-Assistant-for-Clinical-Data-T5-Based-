#!/usr/bin/env python3
"""
Database Viewer Utility
Provides functionality to explore database structure and data for the UI.
"""

import os
import sys
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path for imports
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

logger = logging.getLogger(__name__)

class DatabaseViewer:
    """Database viewer utility for exploring database structure and data."""
    
    def __init__(self, connection_params: Optional[Dict[str, Any]] = None):
        """Initialize database viewer with connection parameters."""
        self.connection_params = connection_params or self._get_default_connection_params()
        self.connection = None
        self._schema_cache = {}
        
    def _get_default_connection_params(self) -> Dict[str, Any]:
        """Get default database connection parameters."""
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'medical'),
            'user': os.getenv('DB_USERNAME', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'options': f"-c search_path={os.getenv('DB_SCHEMA', 'clinical_data')},public"
        }
    
    def connect(self) -> bool:
        """Establish database connection."""
        try:
            self.connection = psycopg2.connect(**self.connection_params)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def get_schemas(self) -> List[Dict[str, Any]]:
        """Get list of all schemas in the database."""
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT schema_name, 
                           schema_owner,
                           (SELECT COUNT(*) FROM information_schema.tables 
                            WHERE table_schema = schema_name) as table_count
                    FROM information_schema.schemata 
                    WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                    ORDER BY schema_name;
                """)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting schemas: {e}")
            return []
    
    def get_tables(self, schema_name: str = 'clinical_data') -> List[Dict[str, Any]]:
        """Get list of tables in a schema with metadata."""
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        t.table_name,
                        t.table_type,
                        COALESCE(c.column_count, 0) as column_count,
                        COALESCE(r.row_count, 0) as estimated_row_count,
                        pg_size_pretty(pg_total_relation_size(quote_ident(t.table_schema)||'.'||quote_ident(t.table_name))) as table_size
                    FROM information_schema.tables t
                    LEFT JOIN (
                        SELECT table_name, COUNT(*) as column_count
                        FROM information_schema.columns 
                        WHERE table_schema = %s
                        GROUP BY table_name
                    ) c ON t.table_name = c.table_name
                    LEFT JOIN (
                        SELECT 
                            schemaname||'.'||relname as full_name,
                            n_tup_ins + n_tup_upd + n_tup_del as row_count
                        FROM pg_stat_user_tables
                        WHERE schemaname = %s
                    ) r ON (t.table_schema||'.'||t.table_name) = r.full_name
                    WHERE t.table_schema = %s
                    AND t.table_type = 'BASE TABLE'
                    ORDER BY t.table_name;
                """, (schema_name, schema_name, schema_name))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting tables for schema {schema_name}: {e}")
            return []
    
    def get_table_columns(self, table_name: str, schema_name: str = 'clinical_data') -> List[Dict[str, Any]]:
        """Get detailed column information for a table."""
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        c.column_name,
                        c.data_type,
                        c.character_maximum_length,
                        c.numeric_precision,
                        c.numeric_scale,
                        c.is_nullable,
                        c.column_default,
                        c.ordinal_position,
                        CASE 
                            WHEN pk.column_name IS NOT NULL THEN 'PRIMARY KEY'
                            WHEN fk.column_name IS NOT NULL THEN 'FOREIGN KEY'
                            WHEN uk.column_name IS NOT NULL THEN 'UNIQUE'
                            ELSE ''
                        END as constraint_type,
                        fk.foreign_table_name,
                        fk.foreign_column_name
                    FROM information_schema.columns c
                    LEFT JOIN (
                        SELECT ku.column_name
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage ku 
                            ON tc.constraint_name = ku.constraint_name
                        WHERE tc.table_schema = %s 
                            AND tc.table_name = %s 
                            AND tc.constraint_type = 'PRIMARY KEY'
                    ) pk ON c.column_name = pk.column_name
                    LEFT JOIN (
                        SELECT 
                            ku.column_name,
                            ccu.table_name AS foreign_table_name,
                            ccu.column_name AS foreign_column_name
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage ku 
                            ON tc.constraint_name = ku.constraint_name
                        JOIN information_schema.constraint_column_usage ccu 
                            ON ccu.constraint_name = tc.constraint_name
                        WHERE tc.table_schema = %s 
                            AND tc.table_name = %s 
                            AND tc.constraint_type = 'FOREIGN KEY'
                    ) fk ON c.column_name = fk.column_name
                    LEFT JOIN (
                        SELECT ku.column_name
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage ku 
                            ON tc.constraint_name = ku.constraint_name
                        WHERE tc.table_schema = %s 
                            AND tc.table_name = %s 
                            AND tc.constraint_type = 'UNIQUE'
                    ) uk ON c.column_name = uk.column_name
                    WHERE c.table_schema = %s 
                        AND c.table_name = %s
                    ORDER BY c.ordinal_position;
                """, (schema_name, table_name, schema_name, table_name, 
                      schema_name, table_name, schema_name, table_name))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting columns for table {schema_name}.{table_name}: {e}")
            return []
    
    def get_table_sample_data(self, table_name: str, schema_name: str = 'clinical_data', 
                             limit: int = 10) -> pd.DataFrame:
        """Get sample data from a table."""
        if not self.connection:
            if not self.connect():
                return pd.DataFrame()
        
        try:
            query = f"SELECT * FROM {schema_name}.{table_name} LIMIT %s"
            return pd.read_sql_query(query, self.connection, params=[limit])
        except Exception as e:
            logger.error(f"Error getting sample data from {schema_name}.{table_name}: {e}")
            return pd.DataFrame()
    
    def get_table_statistics(self, table_name: str, schema_name: str = 'clinical_data') -> Dict[str, Any]:
        """Get basic statistics for a table."""
        if not self.connection:
            if not self.connect():
                return {}
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get row count
                cursor.execute(f"SELECT COUNT(*) as row_count FROM {schema_name}.{table_name}")
                row_count = cursor.fetchone()['row_count']
                
                # Get table size
                cursor.execute("""
                    SELECT pg_size_pretty(pg_total_relation_size(%s)) as table_size,
                           pg_size_pretty(pg_relation_size(%s)) as data_size
                """, (f"{schema_name}.{table_name}", f"{schema_name}.{table_name}"))
                size_info = cursor.fetchone()
                
                # Get column statistics for numeric columns
                columns = self.get_table_columns(table_name, schema_name)
                numeric_columns = [col['column_name'] for col in columns 
                                 if col['data_type'] in ['integer', 'bigint', 'numeric', 'decimal', 'real', 'double precision']]
                
                column_stats = {}
                if numeric_columns:
                    for col in numeric_columns[:5]:  # Limit to first 5 numeric columns
                        try:
                            cursor.execute(f"""
                                SELECT 
                                    MIN({col}) as min_val,
                                    MAX({col}) as max_val,
                                    AVG({col}) as avg_val,
                                    COUNT(DISTINCT {col}) as distinct_count
                                FROM {schema_name}.{table_name}
                                WHERE {col} IS NOT NULL
                            """)
                            stats = cursor.fetchone()
                            if stats:
                                column_stats[col] = dict(stats)
                        except Exception as e:
                            logger.warning(f"Could not get stats for column {col}: {e}")
                
                return {
                    'row_count': row_count,
                    'table_size': size_info['table_size'],
                    'data_size': size_info['data_size'],
                    'column_statistics': column_stats
                }
        except Exception as e:
            logger.error(f"Error getting statistics for {schema_name}.{table_name}: {e}")
            return {}
    
    def get_foreign_key_relationships(self, schema_name: str = 'clinical_data') -> List[Dict[str, Any]]:
        """Get foreign key relationships in the schema."""
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        tc.table_name as source_table,
                        kcu.column_name as source_column,
                        ccu.table_name as target_table,
                        ccu.column_name as target_column,
                        tc.constraint_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage ccu 
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_schema = %s
                    ORDER BY tc.table_name, kcu.column_name;
                """, (schema_name,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting foreign key relationships: {e}")
            return []
    
    def execute_custom_query(self, query: str, params: Optional[List] = None) -> pd.DataFrame:
        """Execute a custom SQL query and return results as DataFrame."""
        if not self.connection:
            if not self.connect():
                return pd.DataFrame()
        
        try:
            return pd.read_sql_query(query, self.connection, params=params)
        except Exception as e:
            logger.error(f"Error executing custom query: {e}")
            return pd.DataFrame()
    
    def get_database_overview(self) -> Dict[str, Any]:
        """Get a comprehensive overview of the database."""
        overview = {
            'schemas': self.get_schemas(),
            'connection_status': self.connection is not None,
            'total_tables': 0,
            'total_columns': 0,
            'relationships': []
        }
        
        # Get detailed info for clinical_data schema
        clinical_tables = self.get_tables('clinical_data')
        overview['clinical_data_tables'] = clinical_tables
        overview['total_tables'] = len(clinical_tables)
        
        # Count total columns
        total_columns = 0
        for table in clinical_tables:
            columns = self.get_table_columns(table['table_name'], 'clinical_data')
            total_columns += len(columns)
        
        overview['total_columns'] = total_columns
        overview['relationships'] = self.get_foreign_key_relationships('clinical_data')
        
        return overview
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()