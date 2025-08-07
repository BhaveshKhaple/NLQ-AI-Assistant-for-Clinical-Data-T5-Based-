#!/usr/bin/env python3
"""
Test the corrected vaccine query with updated schema descriptions
"""

import sys
import os
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / 'src')
sys.path.insert(0, src_path)

def test_corrected_vaccine_query():
    """Test that the corrected query works"""
    
    print("🧪 Testing Corrected Vaccine Query")
    print("=" * 40)
    
    try:
        from nlq.database_executor import DatabaseExecutor
        
        db_executor = DatabaseExecutor()
        if not db_executor.connect():
            print("❌ Failed to connect to database")
            return False
        
        print("✅ Database connected successfully")
        
        # Test the corrected query
        print("\n1. 🔍 Testing corrected vaccine query...")
        corrected_query = "SELECT DISTINCT description FROM clinical_data.immunizations;"
        
        result = db_executor.execute_query(corrected_query)
        
        print(f"   📊 Query: {corrected_query}")
        print(f"   ✅ Success: {result.get('success', False)}")
        
        if result.get('success'):
            data = result.get('data', [])
            print(f"   📋 Vaccine types found: {len(data)}")
            
            # Show first few vaccine types
            if data:
                print("\n   🔍 Sample vaccine types:")
                for i, row in enumerate(data[:5], 1):
                    vaccine_name = row.get('description', 'N/A')
                    print(f"   {i}. {vaccine_name}")
                
                if len(data) > 5:
                    print(f"   ... and {len(data) - 5} more")
            
            return True
        else:
            print(f"   ❌ Query failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_vaccine_statistics():
    """Test vaccine statistics query"""
    
    print("\n🧪 Testing Vaccine Statistics")
    print("=" * 40)
    
    try:
        from nlq.database_executor import DatabaseExecutor
        
        db_executor = DatabaseExecutor()
        if not db_executor.connect():
            print("❌ Failed to connect to database")
            return False
        
        # Test vaccine statistics
        print("1. 📊 Testing vaccine statistics query...")
        stats_query = """
        SELECT description as vaccine_name, COUNT(*) as count 
        FROM clinical_data.immunizations 
        GROUP BY description 
        ORDER BY count DESC 
        LIMIT 10;
        """
        
        result = db_executor.execute_query(stats_query)
        
        if result.get('success'):
            data = result.get('data', [])
            print(f"   ✅ Found statistics for {len(data)} vaccine types")
            
            if data:
                print("\n   📊 Top vaccines by frequency:")
                for i, row in enumerate(data, 1):
                    vaccine_name = row.get('vaccine_name', 'N/A')
                    count = row.get('count', 0)
                    print(f"   {i}. {vaccine_name}: {count} administrations")
            
            return True
        else:
            print(f"   ❌ Statistics query failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Statistics test failed: {e}")
        return False

def test_schema_description_update():
    """Test that the schema descriptions were updated correctly"""
    
    print("\n🧪 Testing Schema Description Update")
    print("=" * 40)
    
    try:
        import json
        
        # Load the updated schema
        schema_path = "d:/projects/healthca/data/processed/database_schema.json"
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        # Find immunizations descriptions
        immunizations_descriptions = []
        for item in schema.get('enhanced_descriptions', []):
            if item.get('table') == 'immunizations':
                immunizations_descriptions.append(item)
        
        print(f"✅ Found {len(immunizations_descriptions)} immunizations descriptions")
        
        # Check for the updated description column
        description_col = None
        for item in immunizations_descriptions:
            if item.get('column') == 'description':
                description_col = item
                break
        
        if description_col:
            desc_text = description_col.get('description', '')
            print(f"✅ Found description column entry")
            print(f"   📝 Description: {desc_text[:100]}...")
            
            # Check if it mentions vaccine names
            if 'vaccine' in desc_text.lower():
                print("   ✅ Description mentions vaccines")
                return True
            else:
                print("   ⚠️ Description doesn't mention vaccines clearly")
                return False
        else:
            print("   ❌ Description column entry not found")
            return False
            
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing Corrected Vaccine Query")
    print("=" * 50)
    
    # Test 1: Corrected query
    query_ok = test_corrected_vaccine_query()
    
    # Test 2: Vaccine statistics
    stats_ok = test_vaccine_statistics()
    
    # Test 3: Schema description update
    schema_ok = test_schema_description_update()
    
    print("\n" + "=" * 50)
    print("📊 Final Results:")
    print(f"Corrected Query: {'✅ PASS' if query_ok else '❌ FAIL'}")
    print(f"Vaccine Statistics: {'✅ PASS' if stats_ok else '❌ FAIL'}")
    print(f"Schema Update: {'✅ PASS' if schema_ok else '❌ FAIL'}")
    
    if all([query_ok, stats_ok, schema_ok]):
        print("\n🎉 All tests passed!")
        print("✅ Corrected query works: SELECT DISTINCT description FROM clinical_data.immunizations")
        print("✅ Schema descriptions updated to clarify vaccine names")
        print("✅ AI should now generate correct vaccine queries")
    else:
        print("\n⚠️ Some tests failed. Check the issues above.")