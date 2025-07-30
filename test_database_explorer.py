#!/usr/bin/env python3
"""
Test script for Database Explorer functionality
"""

import os
import sys
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / "src")
sys.path.insert(0, src_path)

from database.database_viewer import DatabaseViewer

def test_database_connection():
    """Test database connection and basic functionality."""
    print("🧪 Testing Database Explorer...")
    
    # Test database connection
    print("\n1. Testing database connection...")
    db_viewer = DatabaseViewer()
    
    if db_viewer.connect():
        print("✅ Database connection successful!")
        
        # Test getting schemas
        print("\n2. Testing schema retrieval...")
        schemas = db_viewer.get_schemas()
        print(f"Found {len(schemas)} schemas:")
        for schema in schemas:
            print(f"  - {schema['schema_name']} ({schema['table_count']} tables)")
        
        # Test getting tables
        print("\n3. Testing table retrieval...")
        tables = db_viewer.get_tables('clinical_data')
        print(f"Found {len(tables)} tables in clinical_data schema:")
        for table in tables[:5]:  # Show first 5 tables
            print(f"  - {table['table_name']} ({table['column_count']} columns, ~{table['estimated_row_count']} rows)")
        
        # Test getting columns for a table
        if tables:
            test_table = tables[0]['table_name']
            print(f"\n4. Testing column retrieval for '{test_table}'...")
            columns = db_viewer.get_table_columns(test_table)
            print(f"Found {len(columns)} columns:")
            for col in columns[:3]:  # Show first 3 columns
                print(f"  - {col['column_name']} ({col['data_type']}) {'[PK]' if col['constraint_type'] == 'PRIMARY KEY' else ''}")
        
        # Test getting relationships
        print("\n5. Testing relationship retrieval...")
        relationships = db_viewer.get_foreign_key_relationships()
        print(f"Found {len(relationships)} foreign key relationships:")
        for rel in relationships[:3]:  # Show first 3 relationships
            print(f"  - {rel['source_table']}.{rel['source_column']} -> {rel['target_table']}.{rel['target_column']}")
        
        # Test database overview
        print("\n6. Testing database overview...")
        overview = db_viewer.get_database_overview()
        print(f"Database overview: {overview['total_tables']} tables, {overview['total_columns']} columns")
        
        db_viewer.disconnect()
        print("\n✅ All tests passed! Database Explorer is ready to use.")
        return True
        
    else:
        print("❌ Database connection failed!")
        print("Please check your database configuration in the .env file or config.yaml")
        return False

if __name__ == "__main__":
    success = test_database_connection()
    if success:
        print("\n🎉 Database Explorer is ready!")
        print("You can now run the Streamlit app to explore your database:")
        print("streamlit run src/ui/streamlit_app.py")
    else:
        print("\n💡 To fix database connection issues:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check your database credentials in .env file")
        print("3. Ensure the clinical_data schema exists and has data")