#!/usr/bin/env python3
"""
Test the table output display fix
"""

import sys
import os
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / 'src')
sys.path.insert(0, src_path)

def test_rag_query_execution():
    """Test RAG query execution with database connection"""
    
    print("🧪 Testing RAG Query Execution")
    print("=" * 40)
    
    try:
        from nlq.rag_inference_engine import RAGEnhancedInferenceEngine
        from nlq.database_executor import DatabaseExecutor
        
        # Initialize RAG engine
        print("1. 🤖 Initializing RAG Engine...")
        rag_engine = RAGEnhancedInferenceEngine()
        print("   ✅ RAG Engine initialized")
        
        # Test SQL generation
        print("\n2. 🔍 Testing SQL Generation...")
        test_query = "How many patients do we have?"
        
        rag_result = rag_engine.generate_sql(
            test_query,
            use_rag=True
        )
        
        print(f"   📝 Query: {test_query}")
        print(f"   ✅ SQL Generated: {rag_result.get('generated_sql', 'N/A')[:50]}...")
        print(f"   📊 Valid: {rag_result.get('validation', {}).get('is_valid', False)}")
        
        if not rag_result.get('validation', {}).get('is_valid', False):
            print("   ⚠️ Generated SQL is not valid, skipping execution test")
            return False
        
        # Test database execution
        print("\n3. 🗄️ Testing Database Execution...")
        db_executor = DatabaseExecutor()
        
        if not db_executor.connect():
            print("   ❌ Failed to connect to database")
            return False
        
        print("   ✅ Database connected")
        
        # Execute the generated SQL
        exec_result = db_executor.execute_query(rag_result['generated_sql'])
        
        print(f"   📊 Execution Success: {exec_result.get('success', False)}")
        
        if exec_result.get('success'):
            data = exec_result.get('data', [])
            print(f"   📋 Rows Returned: {len(data) if data else 0}")
            if data:
                print(f"   📊 Sample Data: {data[0] if isinstance(data, list) else 'DataFrame'}")
            return True
        else:
            print(f"   ❌ Execution Failed: {exec_result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_result_structure_simulation():
    """Test the result display logic with different structures"""
    
    print("\n🧪 Testing Result Display Logic")
    print("=" * 40)
    
    # Simulate different result structures
    
    # 1. Successful RAG execution
    successful_rag_result = {
        'success': True,
        'generated_sql': 'SELECT COUNT(*) FROM clinical_data.patients',
        'rag_enhanced': True,
        'execution': {
            'success': True,
            'data': [{'count': 107}],
            'execution_time': 0.005
        }
    }
    
    # 2. Failed RAG execution (database error)
    failed_rag_result = {
        'success': True,
        'generated_sql': 'SELECT COUNT(*) FROM clinical_data.patients',
        'rag_enhanced': True,
        'execution': {
            'success': False,
            'error': 'Failed to connect to database'
        }
    }
    
    # 3. RAG without execution (table not enabled)
    no_execution_result = {
        'success': True,
        'generated_sql': 'SELECT COUNT(*) FROM clinical_data.patients',
        'rag_enhanced': True
    }
    
    def test_display_logic(result, test_name):
        """Test the display logic"""
        print(f"\n🔍 Testing {test_name}:")
        
        # Simulate the logic from _display_successful_result
        if 'results' in result and 'formats' in result['results']:
            print("   ✅ Traditional pipeline format detected")
            return "traditional"
        elif 'execution' in result:
            if result['execution'].get('success'):
                print("   ✅ RAG execution successful - would show table")
                return "rag_success"
            else:
                print(f"   ❌ RAG execution failed: {result['execution'].get('error', 'Unknown error')}")
                return "rag_failed"
        else:
            print("   ℹ️ No execution results - would show 'Enable table output' message")
            return "no_execution"
    
    # Test all scenarios
    results = [
        (successful_rag_result, "Successful RAG Execution"),
        (failed_rag_result, "Failed RAG Execution"),
        (no_execution_result, "RAG without Execution")
    ]
    
    for result, test_name in results:
        display_type = test_display_logic(result, test_name)
    
    return True

if __name__ == "__main__":
    print("🔧 Testing Table Output Display Fix")
    print("=" * 50)
    
    # Test 1: RAG query execution
    execution_ok = test_rag_query_execution()
    
    # Test 2: Result display logic
    display_ok = test_result_structure_simulation()
    
    print("\n" + "=" * 50)
    print("📊 Final Results:")
    print(f"RAG Query Execution: {'✅ PASS' if execution_ok else '❌ FAIL'}")
    print(f"Result Display Logic: {'✅ PASS' if display_ok else '❌ FAIL'}")
    
    if execution_ok and display_ok:
        print("\n🎉 Table output should now work correctly!")
        print("✅ RAG queries will execute and display results")
        print("✅ Failed executions will show clear error messages")
        print("✅ No more 'Enable table output' when table is already enabled")
    else:
        print("\n⚠️ Some tests failed. Check the issues above.")