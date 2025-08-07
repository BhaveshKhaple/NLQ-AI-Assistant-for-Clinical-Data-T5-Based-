#!/usr/bin/env python3
"""
Test the current system state to verify everything is working
"""

import sys
import os
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / 'src')
sys.path.insert(0, src_path)

def test_system_components():
    """Test all system components"""
    
    print("🔧 Testing Current System State")
    print("=" * 50)
    
    results = {}
    
    # Test 1: Environment variables
    print("1. 🌍 Testing environment variables...")
    required_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USERNAME', 'DB_PASSWORD']
    env_ok = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            display_value = "***" if "PASSWORD" in var else value
            print(f"   ✅ {var}: {display_value}")
        else:
            print(f"   ❌ {var}: Not set")
            env_ok = False
    
    results['environment'] = env_ok
    
    # Test 2: Database connection
    print("\n2. 🗄️ Testing database connection...")
    try:
        from nlq.database_executor import DatabaseExecutor
        
        db_executor = DatabaseExecutor()
        if db_executor.connect():
            # Test simple query
            simple_result = db_executor.execute_query("SELECT COUNT(*) as count FROM clinical_data.patients;")
            if simple_result.get('success'):
                count = simple_result['data'][0]['count']
                print(f"   ✅ Database connected: {count} patients")
                results['database'] = True
            else:
                print(f"   ❌ Query failed: {simple_result.get('error')}")
                results['database'] = False
        else:
            print("   ❌ Connection failed")
            results['database'] = False
    except Exception as e:
        print(f"   ❌ Database test failed: {e}")
        results['database'] = False
    
    # Test 3: RAG system
    print("\n3. 🤖 Testing RAG system...")
    try:
        from nlq.rag_inference_engine import RAGEnhancedInferenceEngine
        
        rag_engine = RAGEnhancedInferenceEngine()
        print("   ✅ RAG engine initialized")
        
        # Test SQL generation (without model loading)
        test_result = rag_engine.generate_sql_with_gemini("How many patients do we have?", use_rag=True)
        
        if test_result.get('validation', {}).get('is_valid', False):
            print(f"   ✅ SQL generation works: {test_result.get('generated_sql', 'N/A')[:50]}...")
            results['rag'] = True
        else:
            print("   ⚠️ SQL generation failed (may need model loading)")
            results['rag'] = False
    except Exception as e:
        print(f"   ❌ RAG test failed: {e}")
        results['rag'] = False
    
    # Test 4: Schema descriptions
    print("\n4. 📋 Testing schema descriptions...")
    try:
        import json
        
        schema_path = "d:/projects/healthca/data/processed/database_schema.json"
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        # Check for immunizations table
        immunizations_found = False
        enhanced_desc_found = False
        
        for item in schema:
            if isinstance(item, dict):
                if item.get('table') == 'immunizations' and item.get('column') == 'description':
                    desc_text = item.get('description', '')
                    if 'vaccine' in desc_text.lower():
                        enhanced_desc_found = True
                        break
        
        if enhanced_desc_found:
            print("   ✅ Enhanced schema descriptions found")
            results['schema'] = True
        else:
            print("   ⚠️ Enhanced schema descriptions not found")
            results['schema'] = False
            
    except Exception as e:
        print(f"   ❌ Schema test failed: {e}")
        results['schema'] = False
    
    # Test 5: End-to-end vaccine query
    print("\n5. 💉 Testing end-to-end vaccine query...")
    try:
        from nlq.database_executor import DatabaseExecutor
        
        db_executor = DatabaseExecutor()
        if db_executor.connect():
            vaccine_query = "SELECT DISTINCT description FROM clinical_data.immunizations LIMIT 5;"
            vaccine_result = db_executor.execute_query(vaccine_query)
            
            if vaccine_result.get('success'):
                data = vaccine_result.get('data', [])
                print(f"   ✅ Vaccine query works: {len(data)} vaccine types")
                
                if data:
                    for i, row in enumerate(data[:3], 1):
                        vaccine = row.get('description', 'N/A')
                        print(f"     {i}. {vaccine}")
                
                results['vaccine_query'] = True
            else:
                print(f"   ❌ Vaccine query failed: {vaccine_result.get('error')}")
                results['vaccine_query'] = False
        else:
            print("   ❌ Database connection failed")
            results['vaccine_query'] = False
    except Exception as e:
        print(f"   ❌ Vaccine query test failed: {e}")
        results['vaccine_query'] = False
    
    return results

def generate_system_report(results):
    """Generate a system status report"""
    
    print("\n" + "=" * 50)
    print("📊 System Status Report")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"Overall Status: {passed_tests}/{total_tests} tests passed")
    print()
    
    status_map = {
        'environment': 'Environment Variables',
        'database': 'Database Connection',
        'rag': 'RAG System',
        'schema': 'Schema Descriptions',
        'vaccine_query': 'Vaccine Query'
    }
    
    for key, description in status_map.items():
        status = "✅ PASS" if results.get(key, False) else "❌ FAIL"
        print(f"{description}: {status}")
    
    print("\n" + "=" * 50)
    
    if passed_tests == total_tests:
        print("🎉 All systems operational!")
        print("✅ The 'database execution failed' error should not occur")
        print("✅ Vaccine queries should work correctly")
        print("✅ Table output should display properly")
        print("\n💡 If you're still seeing errors in Streamlit:")
        print("   1. Restart the Streamlit app")
        print("   2. Clear browser cache")
        print("   3. Check Streamlit console for detailed logs")
    else:
        print("⚠️ Some systems have issues!")
        print("\n🔧 Recommended actions:")
        
        if not results.get('environment', False):
            print("   - Check .env file configuration")
        if not results.get('database', False):
            print("   - Verify PostgreSQL is running")
            print("   - Check database credentials")
        if not results.get('rag', False):
            print("   - Check Gemini API key")
            print("   - Verify RAG system configuration")
        if not results.get('schema', False):
            print("   - Update schema descriptions")
        if not results.get('vaccine_query', False):
            print("   - Check immunizations table structure")

if __name__ == "__main__":
    print("🔍 Current System State Analysis")
    print("=" * 60)
    
    results = test_system_components()
    generate_system_report(results)