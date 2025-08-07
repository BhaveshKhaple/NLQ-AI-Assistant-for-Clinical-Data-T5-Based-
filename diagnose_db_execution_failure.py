#!/usr/bin/env python3
"""
Diagnose database execution failure issues
"""

import sys
import os
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / 'src')
sys.path.insert(0, src_path)

def test_database_connection_stability():
    """Test database connection stability and execution"""
    
    print("🔍 Diagnosing Database Execution Failure")
    print("=" * 50)
    
    try:
        from nlq.database_executor import DatabaseExecutor
        
        # Test 1: Basic connection
        print("1. 🔌 Testing basic connection...")
        db_executor = DatabaseExecutor()
        
        connect_result = db_executor.connect()
        print(f"   Connection result: {connect_result}")
        
        if not connect_result:
            print("   ❌ Initial connection failed")
            return False
        
        print("   ✅ Initial connection successful")
        
        # Test 2: Connection state
        print("\n2. 🔍 Checking connection state...")
        if hasattr(db_executor, 'connection') and db_executor.connection:
            print("   ✅ Connection object exists")
            
            # Check if connection is still alive
            try:
                cursor = db_executor.connection.cursor()
                cursor.execute("SELECT 1;")
                result = cursor.fetchone()
                cursor.close()
                print(f"   ✅ Connection is alive: {result}")
            except Exception as e:
                print(f"   ❌ Connection test failed: {e}")
                return False
        else:
            print("   ❌ No connection object found")
            return False
        
        # Test 3: Simple query execution
        print("\n3. 📊 Testing simple query execution...")
        simple_query = "SELECT COUNT(*) as count FROM clinical_data.patients;"
        
        exec_result = db_executor.execute_query(simple_query)
        print(f"   Query: {simple_query}")
        print(f"   Success: {exec_result.get('success', False)}")
        
        if exec_result.get('success'):
            data = exec_result.get('data', [])
            print(f"   Result: {data}")
        else:
            print(f"   Error: {exec_result.get('error', 'Unknown error')}")
            return False
        
        # Test 4: Multiple consecutive queries
        print("\n4. 🔄 Testing multiple consecutive queries...")
        queries = [
            "SELECT COUNT(*) as count FROM clinical_data.patients;",
            "SELECT COUNT(*) as count FROM clinical_data.conditions;",
            "SELECT COUNT(*) as count FROM clinical_data.immunizations;"
        ]
        
        for i, query in enumerate(queries, 1):
            result = db_executor.execute_query(query)
            success = result.get('success', False)
            print(f"   Query {i}: {'✅' if success else '❌'} {success}")
            
            if not success:
                print(f"   Error: {result.get('error', 'Unknown error')}")
                return False
        
        # Test 5: Connection after multiple queries
        print("\n5. 🔍 Checking connection after multiple queries...")
        try:
            cursor = db_executor.connection.cursor()
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()
            cursor.close()
            print(f"   ✅ Connection still alive: {result}")
        except Exception as e:
            print(f"   ❌ Connection lost after queries: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Diagnosis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_streamlit_execution_flow():
    """Test the exact execution flow used in Streamlit"""
    
    print("\n🧪 Testing Streamlit Execution Flow")
    print("=" * 40)
    
    try:
        # Simulate what happens in Streamlit app
        print("1. 🤖 Simulating Streamlit RAG execution flow...")
        
        # Step 1: Create DatabaseExecutor (like in Streamlit)
        from nlq.database_executor import DatabaseExecutor
        db_executor = DatabaseExecutor()
        print("   ✅ DatabaseExecutor created")
        
        # Step 2: Connect (like in Streamlit fix)
        if db_executor.connect():
            print("   ✅ Database connected")
        else:
            print("   ❌ Database connection failed")
            return False
        
        # Step 3: Execute query (like in Streamlit)
        test_sql = "SELECT DISTINCT description FROM clinical_data.immunizations LIMIT 5;"
        print(f"   📊 Executing: {test_sql}")
        
        exec_result = db_executor.execute_query(test_sql)
        
        print(f"   Success: {exec_result.get('success', False)}")
        
        if exec_result.get('success'):
            data = exec_result.get('data', [])
            print(f"   📋 Rows returned: {len(data) if data else 0}")
            
            if data:
                print("   🔍 Sample results:")
                for i, row in enumerate(data[:3], 1):
                    vaccine = row.get('description', 'N/A')
                    print(f"     {i}. {vaccine}")
            
            # Step 4: Simulate result structure (like in Streamlit)
            result_structure = {
                'success': True,
                'generated_sql': test_sql,
                'execution': exec_result,
                'rag_enhanced': True
            }
            
            print("   ✅ Result structure created")
            
            # Step 5: Test display logic (like in _display_successful_result)
            if 'execution' in result_structure and result_structure['execution'].get('success'):
                print("   ✅ Display logic would show table")
                return True
            else:
                print("   ❌ Display logic would show error")
                return False
        else:
            print(f"   ❌ Query execution failed: {exec_result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Streamlit flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_connection_persistence():
    """Test if connection persists across multiple DatabaseExecutor instances"""
    
    print("\n🧪 Testing Connection Persistence")
    print("=" * 40)
    
    try:
        from nlq.database_executor import DatabaseExecutor
        
        # Test 1: First instance
        print("1. 🔌 Testing first DatabaseExecutor instance...")
        db1 = DatabaseExecutor()
        if db1.connect():
            result1 = db1.execute_query("SELECT 1 as test;")
            print(f"   Instance 1: {'✅' if result1.get('success') else '❌'}")
        else:
            print("   ❌ First instance connection failed")
            return False
        
        # Test 2: Second instance (like in Streamlit - new instance each time)
        print("\n2. 🔌 Testing second DatabaseExecutor instance...")
        db2 = DatabaseExecutor()
        if db2.connect():
            result2 = db2.execute_query("SELECT 2 as test;")
            print(f"   Instance 2: {'✅' if result2.get('success') else '❌'}")
        else:
            print("   ❌ Second instance connection failed")
            return False
        
        # Test 3: Third instance with actual query
        print("\n3. 🔌 Testing third instance with real query...")
        db3 = DatabaseExecutor()
        if db3.connect():
            result3 = db3.execute_query("SELECT COUNT(*) as count FROM clinical_data.patients;")
            success = result3.get('success', False)
            print(f"   Instance 3: {'✅' if success else '❌'}")
            
            if success:
                data = result3.get('data', [])
                print(f"   Data: {data}")
                return True
            else:
                print(f"   Error: {result3.get('error', 'Unknown error')}")
                return False
        else:
            print("   ❌ Third instance connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Connection persistence test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Database Execution Failure Diagnosis")
    print("=" * 60)
    
    # Test 1: Connection stability
    stability_ok = test_database_connection_stability()
    
    # Test 2: Streamlit execution flow
    streamlit_ok = test_streamlit_execution_flow()
    
    # Test 3: Connection persistence
    persistence_ok = test_connection_persistence()
    
    print("\n" + "=" * 60)
    print("📊 Diagnosis Results:")
    print(f"Connection Stability: {'✅ PASS' if stability_ok else '❌ FAIL'}")
    print(f"Streamlit Flow: {'✅ PASS' if streamlit_ok else '❌ FAIL'}")
    print(f"Connection Persistence: {'✅ PASS' if persistence_ok else '❌ FAIL'}")
    
    if all([stability_ok, streamlit_ok, persistence_ok]):
        print("\n🎉 All database tests passed!")
        print("✅ Database connection is stable")
        print("✅ Execution flow works correctly")
        print("✅ Multiple instances work properly")
        print("\n💡 The issue might be elsewhere - check Streamlit app logs")
    else:
        print("\n⚠️ Database execution issues found!")
        print("🔧 Recommended fixes:")
        if not stability_ok:
            print("   - Check PostgreSQL service status")
            print("   - Verify database credentials")
        if not streamlit_ok:
            print("   - Review Streamlit execution logic")
            print("   - Check error handling in app")
        if not persistence_ok:
            print("   - Check connection pooling")
            print("   - Verify database connection limits")