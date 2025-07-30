#!/usr/bin/env python3
"""
Test script to simulate UI column functionality
"""

import os
import sys
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / "src")
sys.path.insert(0, src_path)

# Mock streamlit for testing
class MockStreamlit:
    class session_state:
        def __init__(self):
            self.data = {}
        
        def __contains__(self, key):
            return key in self.data
        
        def __getattr__(self, key):
            return self.data.get(key)
        
        def __setattr__(self, key, value):
            if key == 'data':
                super().__setattr__(key, value)
            else:
                self.data[key] = value

    def __init__(self):
        self.session_state = MockStreamlit.session_state()
    
    def error(self, msg): print(f"ERROR: {msg}")
    def warning(self, msg): print(f"WARNING: {msg}")
    def success(self, msg): print(f"SUCCESS: {msg}")
    def info(self, msg): print(f"INFO: {msg}")
    def spinner(self, msg): 
        print(f"SPINNER: {msg}")
        return self
    def __enter__(self): return self
    def __exit__(self, *args): pass

# Mock streamlit
sys.modules['streamlit'] = MockStreamlit()
import streamlit as st

from ui.database_explorer import DatabaseExplorer

def test_ui_columns():
    """Test the UI column functionality."""
    print("🧪 Testing UI Column Functionality...")
    
    # Create database explorer
    explorer = DatabaseExplorer()
    
    # Test initialization
    print("\n1. Testing initialization...")
    if explorer._ensure_db_connection():
        print("✅ Database connection established")
    else:
        print("❌ Database connection failed")
        return False
    
    # Test column rendering (simulate)
    print("\n2. Testing column rendering for 'patients' table...")
    try:
        # This would normally render in Streamlit, but we'll just test the logic
        table_name = 'patients'
        
        if explorer.db_viewer:
            columns = explorer.db_viewer.get_table_columns(table_name)
            print(f"✅ Retrieved {len(columns)} columns")
            
            # Test column data processing
            column_data = []
            for col in columns[:5]:  # Test first 5 columns
                data_type = col['data_type']
                if col.get('character_maximum_length'):
                    data_type += f"({col['character_maximum_length']})"
                elif col.get('numeric_precision'):
                    if col.get('numeric_scale'):
                        data_type += f"({col['numeric_precision']},{col['numeric_scale']})"
                    else:
                        data_type += f"({col['numeric_precision']})"
                
                column_data.append({
                    'Column': col.get('column_name', 'Unknown'),
                    'Type': data_type,
                    'Nullable': '✓' if col.get('is_nullable') == 'YES' else '✗',
                    'Default': col.get('column_default') or '',
                    'Constraint': col.get('constraint_type') or '',
                    'References': f"{col.get('foreign_table_name', '')}.{col.get('foreign_column_name', '')}" 
                                if col.get('foreign_table_name') else ''
                })
            
            print("✅ Column data processing successful")
            print("Sample processed columns:")
            for i, col_data in enumerate(column_data, 1):
                print(f"  {i}. {col_data['Column']:<15} {col_data['Type']:<20} {col_data['Nullable']} {col_data['Constraint']}")
            
            return True
        else:
            print("❌ Database viewer not available")
            return False
            
    except Exception as e:
        print(f"❌ Error in column rendering: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ui_columns()
    if success:
        print("\n🎉 UI Column functionality test passed!")
        print("The Database Explorer columns tab should now work in the web interface.")
        print("\nTo test in the web interface:")
        print("1. Go to http://localhost:8501")
        print("2. Click 'Database Explorer' tab")
        print("3. Click 'Tables' sub-tab")
        print("4. Select 'patients' from dropdown")
        print("5. Click 'Columns' sub-tab")
    else:
        print("\n❌ UI Column functionality test failed!")
        print("There may still be issues with the column display.")