#!/usr/bin/env python3
"""
Simple test to verify database query execution works
"""

import sys
import os
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / 'src')
sys.path.insert(0, src_path)

def test_simple_database_query():
    """Test a simple database query execution"""
    
    print("🧪 Testing Simple Database Query")
    print("=" * 40)
    
    try:
        from nlq.database_executor import DatabaseExecutor
        
        # Initialize and connect
        print("1. 🔌 Connecting to database...")
        db_executor = DatabaseExecutor()
        
        if not db_executor.connect():
            print("   ❌ Failed to connect to database")
            return False
        
        print("   ✅ Database connected successfully")
        
        # Test simple query
        print("\n2. 🔍 Executing simple query...")
        test_sql = "SELECT COUNT(*) as patient_count FROM clinical_data.patients"
        
        exec_result = db_executor.execute_query(test_sql)
        
        print(f"   📊 Query: {test_sql}")
        print(f"   ✅ Success: {exec_result.get('success', False)}")
        
        if exec_result.get('success'):
            data = exec_result.get('data', [])
            print(f"   📋 Data Type: {type(data)}")
            print(f"   📊 Result: {data}")
            
            if data:
                if isinstance(data, list) and len(data) > 0:
                    patient_count = data[0].get('patient_count', 'N/A')
                    print(f"   👥 Patient Count: {patient_count}")
                else:
                    print(f"   📊 DataFrame Shape: {data.shape if hasattr(data, 'shape') else 'N/A'}")
            
            return True
        else:
            print(f"   ❌ Query failed: {exec_result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rag_result_structure():
    """Test creating a proper RAG result structure"""
    
    print("\n🧪 Testing RAG Result Structure")
    print("=" * 40)
    
    try:
        from nlq.database_executor import DatabaseExecutor
        
        # Simulate what happens in the Streamlit app
        print("1. 🤖 Simulating RAG query processing...")
        
        # Mock RAG result (what comes from RAG engine)
        rag_result = {
            'validation': {'is_valid': True},
            'generated_sql': 'SELECT COUNT(*) as patient_count FROM clinical_data.patients',
            'nlq': 'How many patients do we have?',
            'metadata': {'method': 'rag_gemini_enhanced'},
            'generation_time': 1.2
        }
        
        # Convert to pipeline format (what Streamlit app does)
        result = {
            'success': rag_result['validation']['is_valid'],
            'generated_sql': rag_result['generated_sql'],
            'nlq': rag_result['nlq'],
            'metadata': rag_result['metadata'],
            'validation': rag_result['validation'],
            'generation_time': rag_result['generation_time'],
            'rag_enhanced': True
        }
        
        print("   ✅ RAG result converted to pipeline format")
        
        # Execute SQL (what Streamlit app does when table output is enabled)
        print("\n2. 🗄️ Executing SQL with database...")
        
        db_executor = DatabaseExecutor()
        if db_executor.connect():
            exec_result = db_executor.execute_query(result['generated_sql'])
            result['execution'] = exec_result
            print("   ✅ SQL executed and added to result")
        else:
            result['execution'] = {'success': False, 'error': 'Failed to connect to database'}
            print("   ❌ Database connection failed")
        
        # Test display logic (what _display_successful_result does)
        print("\n3. 🖥️ Testing display logic...")
        
        if 'results' in result and 'formats' in result['results']:
            print("   📋 Traditional pipeline format detected")
            display_type = "traditional"
        elif 'execution' in result:
            if result['execution'].get('success'):
                print("   ✅ RAG execution successful - would show table")
                display_type = "rag_success"
                
                # Show what would be displayed
                data = result['execution'].get('data', [])
                print(f"   📊 Would display {len(data) if data else 0} rows")
                if data:
                    print(f"   📋 Sample data: {data[0] if isinstance(data, list) else 'DataFrame'}")
            else:
                print(f"   ❌ RAG execution failed: {result['execution'].get('error', 'Unknown error')}")
                display_type = "rag_failed"
        else:
            print("   ℹ️ No execution results - would show 'Enable table output' message")
            display_type = "no_execution"
        
        return display_type == "rag_success"
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Testing Simple Query Execution")
    print("=" * 50)
    
    # Test 1: Simple database query
    db_ok = test_simple_database_query()
    
    # Test 2: RAG result structure
    rag_ok = test_rag_result_structure()
    
    print("\n" + "=" * 50)
    print("📊 Final Results:")
    print(f"Database Query: {'✅ PASS' if db_ok else '❌ FAIL'}")
    print(f"RAG Result Structure: {'✅ PASS' if rag_ok else '❌ FAIL'}")
    
    if db_ok and rag_ok:
        print("\n🎉 Table output should now work correctly!")
        print("✅ Database queries execute successfully")
        print("✅ RAG results display properly")
        print("✅ No more 'Enable table output' when table is enabled")
    else:
        print("\n⚠️ Some tests failed. Check the issues above.")