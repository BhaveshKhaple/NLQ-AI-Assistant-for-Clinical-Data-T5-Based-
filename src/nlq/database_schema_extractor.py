#!/usr/bin/env python3
"""
Database Schema Extractor for RAG Enhancement
Extracts database schema information to help with SQL generation.
"""

import os
import json
import logging
import psycopg2
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseSchemaExtractor:
    """
    Extracts database schema information for RAG enhancement.
    """
    
    def __init__(self, 
                 db_host: str = None,
                 db_port: str = None,
                 db_name: str = None,
                 db_user: str = None,
                 db_password: str = None):
        """
        Initialize database connection parameters.
        """
        self.db_host = db_host or os.getenv('DB_HOST', 'localhost')
        self.db_port = db_port or os.getenv('DB_PORT', '5432')
        self.db_name = db_name or os.getenv('DB_NAME', 'medical')
        self.db_user = db_user or os.getenv('DB_USER', 'postgres')
        self.db_password = db_password or os.getenv('DB_PASSWORD', 'Pass@123')
        
        self.connection = None
        self.schema_info = {}
    
    def connect(self) -> bool:
        """
        Connect to the database.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.connection = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password
            )
            logger.info("✅ Database connection established")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def extract_schema_info(self) -> Dict[str, Any]:
        """
        Extract comprehensive schema information from the database.
        
        Returns:
            Dict containing schema information
        """
        if not self.connection:
            if not self.connect():
                return {}
        
        try:
            cursor = self.connection.cursor()
            
            # Get all tables in clinical_data schema
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'clinical_data'
                ORDER BY table_name;
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            logger.info(f"📊 Found {len(tables)} tables in clinical_data schema")
            
            schema_info = {
                'schema_name': 'clinical_data',
                'tables': {},
                'relationships': [],
                'schema_descriptions': []
            }
            
            # Extract detailed information for each table
            for table_name in tables:
                try:
                    logger.info(f"📊 Processing table: {table_name}")
                    table_info = self._extract_table_info(cursor, table_name)
                    schema_info['tables'][table_name] = table_info
                    
                    # Create schema descriptions for embeddings
                    schema_descriptions = self._create_schema_descriptions(table_name, table_info)
                    schema_info['schema_descriptions'].extend(schema_descriptions)
                    logger.info(f"✅ Processed table {table_name} with {len(table_info['columns'])} columns")
                except Exception as e:
                    logger.error(f"❌ Error processing table {table_name}: {e}")
                    continue
            
            # Extract foreign key relationships
            try:
                relationships = self._extract_relationships(cursor)
                schema_info['relationships'] = relationships
                
                # Add relationship descriptions
                for rel in relationships:
                    rel_desc = f"Table {rel['table']} column {rel['column']} references {rel['referenced_table']} column {rel['referenced_column']}"
                    schema_info['schema_descriptions'].append({
                        'type': 'relationship',
                        'description': rel_desc,
                        'table': rel['table'],
                        'referenced_table': rel['referenced_table']
                    })
            except Exception as e:
                logger.error(f"❌ Error extracting relationships: {e}")
                schema_info['relationships'] = []
            
            cursor.close()
            self.schema_info = schema_info
            
            logger.info(f"✅ Extracted schema info for {len(tables)} tables with {len(relationships)} relationships")
            return schema_info
            
        except Exception as e:
            logger.error(f"❌ Error extracting schema info: {e}")
            return {}
    
    def _extract_table_info(self, cursor, table_name: str) -> Dict[str, Any]:
        """
        Extract detailed information for a specific table.
        """
        # Get column information
        cursor.execute("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns 
            WHERE table_schema = 'clinical_data' 
            AND table_name = %s
            ORDER BY ordinal_position;
        """, (table_name,))
        
        columns = []
        column_rows = cursor.fetchall()
        for row in column_rows:
            try:
                column_info = {
                    'name': row[0] if len(row) > 0 else 'unknown',
                    'type': row[1] if len(row) > 1 else 'unknown',
                    'nullable': row[2] == 'YES' if len(row) > 2 else True,
                    'default': row[3] if len(row) > 3 else None,
                    'max_length': row[4] if len(row) > 4 else None,
                    'precision': row[5] if len(row) > 5 else None,
                    'scale': row[6] if len(row) > 6 else None
                }
                columns.append(column_info)
            except Exception as e:
                logger.warning(f"Error processing column info for {table_name}: {e}")
                continue
        
        # Get primary key information
        try:
            cursor.execute("""
                SELECT column_name
                FROM information_schema.key_column_usage
                WHERE table_schema = 'clinical_data'
                AND table_name = %s
                AND constraint_name LIKE '%_pkey';
            """, (table_name,))
            
            pk_rows = cursor.fetchall()
            primary_keys = [row[0] for row in pk_rows if len(row) > 0]
        except Exception as e:
            logger.warning(f"Could not get primary keys for {table_name}: {e}")
            primary_keys = []
        
        # Get table row count (approximate)
        try:
            cursor.execute(f"SELECT COUNT(*) FROM clinical_data.{table_name};")
            result = cursor.fetchone()
            row_count = result[0] if result else 0
        except Exception as e:
            logger.warning(f"Could not get row count for {table_name}: {e}")
            row_count = 0
        
        return {
            'columns': columns,
            'primary_keys': primary_keys,
            'row_count': row_count
        }
    
    def _extract_relationships(self, cursor) -> List[Dict[str, str]]:
        """
        Extract foreign key relationships.
        """
        cursor.execute("""
            SELECT
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS referenced_table,
                ccu.column_name AS referenced_column
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'clinical_data';
        """)
        
        relationships = []
        for row in cursor.fetchall():
            relationships.append({
                'table': row[0],
                'column': row[1],
                'referenced_table': row[2],
                'referenced_column': row[3]
            })
        
        return relationships
    
    def _create_schema_descriptions(self, table_name: str, table_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create natural language descriptions of schema elements for embeddings.
        """
        descriptions = []
        
        # Table description
        column_names = [col['name'] for col in table_info['columns']]
        table_desc = f"Table {table_name} contains columns: {', '.join(column_names)}"
        descriptions.append({
            'type': 'table',
            'description': table_desc,
            'table': table_name,
            'columns': column_names
        })
        
        # Column descriptions
        for col in table_info['columns']:
            col_desc = f"Column {col['name']} in table {table_name} is of type {col['type']}"
            if col['name'] in table_info['primary_keys']:
                col_desc += " (primary key)"
            if not col['nullable']:
                col_desc += " (not null)"
            
            descriptions.append({
                'type': 'column',
                'description': col_desc,
                'table': table_name,
                'column': col['name'],
                'data_type': col['type']
            })
        
        # Common query patterns for this table
        if table_name == 'patients':
            descriptions.append({
                'type': 'query_pattern',
                'description': f"To count patients use: SELECT COUNT(*) FROM clinical_data.{table_name}",
                'table': table_name,
                'pattern': 'count'
            })
            descriptions.append({
                'type': 'query_pattern',
                'description': f"To find patients by gender use: SELECT * FROM clinical_data.{table_name} WHERE gender = 'value'",
                'table': table_name,
                'pattern': 'filter'
            })
        elif table_name == 'conditions':
            descriptions.append({
                'type': 'query_pattern',
                'description': f"To find conditions use: SELECT * FROM clinical_data.{table_name} WHERE description LIKE '%condition%'",
                'table': table_name,
                'pattern': 'search'
            })
        elif table_name == 'medications':
            descriptions.append({
                'type': 'query_pattern',
                'description': f"To find medications use: SELECT * FROM clinical_data.{table_name} WHERE description LIKE '%medication%'",
                'table': table_name,
                'pattern': 'search'
            })
        
        return descriptions
    
    def save_schema_info(self, output_path: str = "d:/projects/healthca/data/processed/database_schema.json"):
        """
        Save extracted schema information to a JSON file.
        """
        if not self.schema_info:
            self.extract_schema_info()
        
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.schema_info, f, indent=2, default=str)
            
            logger.info(f"✅ Schema information saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving schema info: {e}")
            return False
    
    def get_schema_embeddings_data(self) -> List[Dict[str, Any]]:
        """
        Get schema descriptions formatted for embedding creation.
        
        Returns:
            List of dictionaries with description and metadata
        """
        if not self.schema_info:
            self.extract_schema_info()
        
        return self.schema_info.get('schema_descriptions', [])
    
    def close(self):
        """
        Close database connection.
        """
        if self.connection:
            self.connection.close()
            logger.info("🔌 Database connection closed")

if __name__ == "__main__":
    # Test the schema extractor
    extractor = DatabaseSchemaExtractor()
    schema_info = extractor.extract_schema_info()
    
    if schema_info:
        print(f"✅ Extracted schema for {len(schema_info['tables'])} tables")
        print(f"📊 Generated {len(schema_info['schema_descriptions'])} schema descriptions")
        
        # Save to file
        extractor.save_schema_info()
        
        # Show some examples
        print("\n🔍 Sample schema descriptions:")
        for i, desc in enumerate(schema_info['schema_descriptions'][:5]):
            print(f"{i+1}. {desc['description']}")
    
    extractor.close()