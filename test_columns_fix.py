#!/usr/bin/env python3
"""
Test script to verify column functionality is working
"""

import os
import sys
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / "src")
sys.path.insert(0, src_path)

from database.database_viewer import DatabaseViewer

def test_columns_functionality():
    """Test the column functionality specifically."""
    print("🧪 Testing Column Functionality Fix...")
    
    with DatabaseViewer() as db_viewer:
        if not db_viewer.connection:
            print("❌ Failed to connect to database")
            return False
        
        print("✅ Database connected successfully")
        
        # Test getting columns for patients table
        print("\n📋 Testing patients table columns...")
        columns = db_viewer.get_table_columns('patients')
        
        if columns:
            print(f"✅ Found {len(columns)} columns in patients table:")
            
            # Show first 10 columns with details
            for i, col in enumerate(columns[:10], 1):
                constraint = f" [{col['constraint_type']}]" if col['constraint_type'] else ""
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                
                print(f"  {i:2d}. {col['column_name']:<20} {col['data_type']:<15} {nullable:<8}{constraint}{default}")
            
            if len(columns) > 10:
                print(f"      ... and {len(columns) - 10} more columns")
            
            # Test a few more tables
            test_tables = ['conditions', 'medications', 'encounters']
            print(f"\n🔍 Testing other tables...")
            
            for table in test_tables:
                cols = db_viewer.get_table_columns(table)
                print(f"  {table:<15}: {len(cols)} columns")
            
            print(f"\n✅ Column functionality is working correctly!")
            return True
        else:
            print("❌ No columns found - there might be an issue")
            return False

if __name__ == "__main__":
    success = test_columns_functionality()
    if success:
        print("\n🎉 Column functionality test passed!")
        print("The Database Explorer columns tab should now work properly.")
        print("Try accessing: http://localhost:8501")
    else:
        print("\n❌ Column functionality test failed!")
        print("Please check the database connection and schema.")