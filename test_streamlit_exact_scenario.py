#!/usr/bin/env python3
"""
Test the exact scenario that happens in Streamlit
"""

import sys
import os
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / 'src')
sys.path.insert(0, src_path)

def test_exact_streamlit_scenario():
    """Test the exact scenario that happens in Streamlit"""
    
    print("🧪 Testing Exact Streamlit Scenario")
    print("=" * 50)
    
    try:
        # Step 1: Simulate RAG SQL generation
        print("1. 🤖 Simulating RAG SQL generation...")
        
        # Mock RAG result (what would come from RAG engine)
        rag_result = {
            'validation': {'is_valid': True},
            'generated_sql': 'SELECT DISTINCT description FROM clinical_data.immunizations LIMIT 10;',
            'nlq': 'What vaccines are available?',
            'metadata': {'method': 'rag_gemini_enhanced'},
            'generation_time': 1.2
        }
        
        print(f"   ✅ Generated SQL: {rag_result['generated_sql']}")
        print(f"   ✅ Valid: {rag_result['validation']['is_valid']}")
        
        # Step 2: Convert RAG result to pipeline format (exact Streamlit code)
        print("\n2. 🔄 Converting to pipeline format...")
        
        result = {
            'success': rag_result['validation']['is_valid'],
            'generated_sql': rag_result['generated_sql'],
            'nlq': rag_result['nlq'],
            'metadata': rag_result['metadata'],
            'validation': rag_result['validation'],
            'generation_time': rag_result['generation_time'],
            'rag_enhanced': True
        }
        
        print(f"   ✅ Result success: {result['success']}")
        
        # Step 3: Execute SQL if valid and table output requested (exact Streamlit code)
        output_formats = ['table']  # Simulate table output enabled
        
        print(f"\n3. 🗄️ Executing SQL (table in output_formats: {'table' in output_formats})...")
        
        if result['success'] and 'table' in output_formats:
            try:
                print("   📦 Importing DatabaseExecutor...")
                from nlq.database_executor import DatabaseExecutor
                
                print("   🔧 Creating DatabaseExecutor instance...")
                db_executor = DatabaseExecutor()
                
                print("   🔌 Connecting to database...")
                connect_success = db_executor.connect()
                print(f"   Connection result: {connect_success}")
                
                if connect_success:
                    print(f"   📊 Executing query: {result['generated_sql']}")
                    exec_result = db_executor.execute_query(result['generated_sql'])
                    
                    print(f"   Execution success: {exec_result.get('success', False)}")
                    
                    if exec_result.get('success'):
                        data = exec_result.get('data', [])
                        print(f"   📋 Rows returned: {len(data) if data else 0}")
                        
                        if data:
                            print("   🔍 Sample data:")
                            for i, row in enumerate(data[:3], 1):
                                vaccine = row.get('description', 'N/A')
                                print(f"     {i}. {vaccine}")
                    else:
                        print(f"   ❌ Execution error: {exec_result.get('error', 'Unknown error')}")
                    
                    result['execution'] = exec_result
                else:
                    print("   ❌ Database connection failed")
                    result['execution'] = {'success': False, 'error': 'Failed to connect to database'}
                    
            except Exception as e:
                print(f"   ❌ Exception during execution: {e}")
                import traceback
                traceback.print_exc()
                result['execution'] = {'success': False, 'error': str(e)}
        else:
            print("   ⚠️ Skipping execution (conditions not met)")
        
        # Step 4: Test display logic (what _display_successful_result would do)
        print("\n4. 🖥️ Testing display logic...")
        
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
            else:
                error_msg = result['execution'].get('error', 'Unknown database error')
                print(f"   ❌ RAG execution failed: {error_msg}")
                display_type = "rag_failed"
        else:
            print("   ℹ️ No execution results - would show 'Enable table output' message")
            display_type = "no_execution"
        
        print(f"\n📊 Final display type: {display_type}")
        
        return display_type == "rag_success"
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_executor_isolation():
    """Test DatabaseExecutor in isolation to ensure it works"""
    
    print("\n🧪 Testing DatabaseExecutor in Isolation")
    print("=" * 45)
    
    try:
        from nlq.database_executor import DatabaseExecutor
        
        print("1. 🔧 Creating DatabaseExecutor...")
        db_executor = DatabaseExecutor()
        
        print("2. 🔌 Connecting...")
        if not db_executor.connect():
            print("   ❌ Connection failed")
            return False
        
        print("   ✅ Connected successfully")
        
        print("3. 📊 Testing simple query...")
        simple_result = db_executor.execute_query("SELECT 1 as test;")
        
        if simple_result.get('success'):
            print(f"   ✅ Simple query worked: {simple_result.get('data')}")
        else:
            print(f"   ❌ Simple query failed: {simple_result.get('error')}")
            return False
        
        print("4. 📊 Testing vaccine query...")
        vaccine_query = "SELECT DISTINCT description FROM clinical_data.immunizations LIMIT 5;"
        vaccine_result = db_executor.execute_query(vaccine_query)
        
        if vaccine_result.get('success'):
            data = vaccine_result.get('data', [])
            print(f"   ✅ Vaccine query worked: {len(data)} rows")
            
            if data:
                for i, row in enumerate(data[:3], 1):
                    vaccine = row.get('description', 'N/A')
                    print(f"     {i}. {vaccine}")
        else:
            print(f"   ❌ Vaccine query failed: {vaccine_result.get('error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ DatabaseExecutor isolation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Testing Exact Streamlit Scenario")
    print("=" * 60)
    
    # Test 1: Exact Streamlit scenario
    streamlit_ok = test_exact_streamlit_scenario()
    
    # Test 2: DatabaseExecutor in isolation
    db_isolation_ok = test_database_executor_isolation()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"Streamlit Scenario: {'✅ PASS' if streamlit_ok else '❌ FAIL'}")
    print(f"DatabaseExecutor Isolation: {'✅ PASS' if db_isolation_ok else '❌ FAIL'}")
    
    if streamlit_ok and db_isolation_ok:
        print("\n🎉 All tests passed!")
        print("✅ Streamlit execution flow works correctly")
        print("✅ DatabaseExecutor works in isolation")
        print("\n💡 If you're still seeing 'database execution failed' in Streamlit:")
        print("   - Check Streamlit console logs for detailed errors")
        print("   - Verify the exact SQL being generated")
        print("   - Check if there are any import or module loading issues")
    else:
        print("\n⚠️ Some tests failed!")
        if not streamlit_ok:
            print("   🔧 Streamlit execution flow has issues")
        if not db_isolation_ok:
            print("   🔧 DatabaseExecutor has issues")