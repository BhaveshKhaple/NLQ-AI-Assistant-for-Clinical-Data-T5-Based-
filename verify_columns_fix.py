#!/usr/bin/env python3
"""
Final verification that the columns functionality is working
"""

import os
import sys
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / "src")
sys.path.insert(0, src_path)

from database.database_viewer import DatabaseViewer

def verify_columns_fix():
    """Verify that the columns functionality is working correctly."""
    print("🔍 Final Verification: Database Explorer Columns Fix")
    print("=" * 60)
    
    # Test 1: Basic database connection
    print("\n1️⃣ Testing Database Connection...")
    try:
        db_viewer = DatabaseViewer()
        if db_viewer.connect():
            print("✅ Database connection successful")
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False
    
    # Test 2: Table listing
    print("\n2️⃣ Testing Table Listing...")
    try:
        tables = db_viewer.get_tables('clinical_data')
        print(f"✅ Found {len(tables)} tables in clinical_data schema")
        
        # Show some key tables
        key_tables = ['patients', 'conditions', 'medications', 'encounters']
        available_tables = [t['table_name'] for t in tables]
        
        for table in key_tables:
            if table in available_tables:
                print(f"   ✓ {table} table available")
            else:
                print(f"   ⚠️ {table} table not found")
    except Exception as e:
        print(f"❌ Table listing error: {e}")
        return False
    
    # Test 3: Column retrieval for patients table
    print("\n3️⃣ Testing Column Retrieval for 'patients' table...")
    try:
        columns = db_viewer.get_table_columns('patients')
        if columns:
            print(f"✅ Retrieved {len(columns)} columns from patients table")
            
            # Show key columns
            key_columns = ['id', 'birth_date', 'gender', 'first_name', 'last_name']
            column_names = [col['column_name'] for col in columns]
            
            print("   Key columns found:")
            for col_name in key_columns:
                if col_name in column_names:
                    col_info = next(col for col in columns if col['column_name'] == col_name)
                    constraint = f" [{col_info['constraint_type']}]" if col_info['constraint_type'] else ""
                    print(f"   ✓ {col_name}: {col_info['data_type']}{constraint}")
                else:
                    print(f"   ⚠️ {col_name}: not found")
        else:
            print("❌ No columns retrieved")
            return False
    except Exception as e:
        print(f"❌ Column retrieval error: {e}")
        return False
    
    # Test 4: Column retrieval for other key tables
    print("\n4️⃣ Testing Column Retrieval for Other Tables...")
    test_tables = ['conditions', 'medications', 'encounters']
    
    for table in test_tables:
        try:
            columns = db_viewer.get_table_columns(table)
            print(f"   ✓ {table}: {len(columns)} columns")
        except Exception as e:
            print(f"   ❌ {table}: error - {e}")
    
    # Test 5: Sample data retrieval
    print("\n5️⃣ Testing Sample Data Retrieval...")
    try:
        sample_data = db_viewer.get_table_sample_data('patients', limit=3)
        if not sample_data.empty:
            print(f"✅ Retrieved {len(sample_data)} sample rows from patients")
            print(f"   Columns in sample: {list(sample_data.columns)[:5]}...")
        else:
            print("⚠️ No sample data retrieved (table might be empty)")
    except Exception as e:
        print(f"❌ Sample data error: {e}")
    
    # Test 6: Database overview
    print("\n6️⃣ Testing Database Overview...")
    try:
        overview = db_viewer.get_database_overview()
        print(f"✅ Database overview generated:")
        print(f"   Total tables: {overview['total_tables']}")
        print(f"   Total columns: {overview['total_columns']}")
        print(f"   Total relationships: {len(overview['relationships'])}")
    except Exception as e:
        print(f"❌ Database overview error: {e}")
    
    # Cleanup
    db_viewer.disconnect()
    
    print("\n" + "=" * 60)
    print("🎉 VERIFICATION COMPLETE!")
    print("\n✅ The Database Explorer columns functionality should now work properly!")
    print("\n📋 To test in the web interface:")
    print("1. Open http://localhost:8501 in your browser")
    print("2. Click on the '🗄️ Database Explorer' tab")
    print("3. Click on the 'Tables' sub-tab")
    print("4. Select 'patients' from the dropdown")
    print("5. Click on the 'Columns' sub-tab")
    print("6. You should see a detailed table with all column information")
    
    print("\n🔧 If you still see issues:")
    print("- Refresh the browser page")
    print("- Check the browser console for any JavaScript errors")
    print("- Try selecting a different table and then back to 'patients'")
    
    return True

if __name__ == "__main__":
    verify_columns_fix()