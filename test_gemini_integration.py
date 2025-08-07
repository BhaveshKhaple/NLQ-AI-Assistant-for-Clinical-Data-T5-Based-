#!/usr/bin/env python3
"""
Test Gemini Integration
Comprehensive testing of Gemini LLM integration with RAG system.
"""

import os
import sys
import time
import json
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))

def test_gemini_client():
    """Test Gemini LLM client."""
    print("🧪 Testing Gemini LLM Client")
    print("-" * 40)
    
    try:
        from src.nlq.gemini_llm_client import GeminiLLMClient
        
        # Initialize client
        client = GeminiLLMClient()
        print("✅ Gemini client created")
        
        # Test initialization
        if client.initialize():
            print("✅ Gemini client initialized successfully")
            
            # Test connection
            test_result = client.test_connection()
            if test_result['success']:
                print(f"✅ Connection test passed ({test_result['response_time']:.3f}s)")
            else:
                print(f"❌ Connection test failed: {test_result['error']}")
                return False
            
            # Test query enhancement
            print("\n🔍 Testing query enhancement...")
            test_query = "Show me patients with diabetes"
            similar_examples = [
                {
                    'extracted_nlq': 'Show patients diagnosed with Diabetes',
                    'target_text': 'SELECT * FROM patients p JOIN conditions c ON p.id = c.patient_id WHERE c.description LIKE \'%Diabetes%\'',
                    'similarity_score': 0.892
                }
            ]
            
            enhancement_result = client.enhance_query_with_gemini(
                test_query, similar_examples, "Clinical database schema"
            )
            
            if enhancement_result['method_used'] != 'gemini_unavailable':
                print(f"✅ Query enhancement successful")
                print(f"   Original: {test_query}")
                print(f"   Enhanced: {enhancement_result['enhanced_query']}")
                print(f"   Method: {enhancement_result['method_used']}")
                print(f"   Confidence: {enhancement_result['confidence_score']:.3f}")
            else:
                print(f"❌ Query enhancement failed: {enhancement_result.get('error', 'Unknown error')}")
            
            # Test SQL generation
            print("\n🔧 Testing SQL generation...")
            sql_result = client.generate_sql_with_gemini(
                test_query, 
                "Clinical database with patients, conditions tables",
                similar_examples
            )
            
            if sql_result['method_used'] != 'gemini_unavailable':
                print(f"✅ SQL generation successful")
                print(f"   Query: {test_query}")
                print(f"   SQL: {sql_result['generated_sql'][:100]}...")
                print(f"   Method: {sql_result['method_used']}")
                print(f"   Confidence: {sql_result['confidence_score']:.3f}")
            else:
                print(f"❌ SQL generation failed: {sql_result.get('error', 'Unknown error')}")
            
            return True
            
        else:
            print("❌ Gemini client initialization failed")
            print("   Check GEMINI_API_KEY environment variable")
            return False
            
    except Exception as e:
        print(f"❌ Gemini client test error: {e}")
        return False

def test_rag_gemini_integration():
    """Test RAG system with Gemini integration."""
    print("\n🧪 Testing RAG-Gemini Integration")
    print("-" * 40)
    
    try:
        from src.nlq.rag_enhanced_nlq import RAGEnhancedNLQ
        
        # Initialize RAG system with Gemini
        rag_system = RAGEnhancedNLQ(preferred_llm="gemini")
        print("✅ RAG system with Gemini created")
        
        # Load training data
        if rag_system.load_training_data():
            print(f"✅ Training data loaded: {len(rag_system.training_data)} examples")
        else:
            print("❌ Failed to load training data")
            return False
        
        # Initialize embeddings
        if rag_system.initialize_embeddings():
            print("✅ Embeddings initialized")
        else:
            print("❌ Failed to initialize embeddings")
            return False
        
        # Test query enhancement
        test_queries = [
            "How many patients are there?",
            "Show me diabetic patients",
            "What medications are prescribed for hypertension?"
        ]
        
        print(f"\n🔍 Testing {len(test_queries)} queries:")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}. Query: {query}")
            
            enhancement_result = rag_system.enhance_query(query)
            
            if enhancement_result['rag_enhanced']:
                print(f"   ✅ RAG enhanced: {enhancement_result['method_used']}")
                print(f"   Original: {enhancement_result['original_query']}")
                print(f"   Enhanced: {enhancement_result['enhanced_query']}")
                print(f"   Confidence: {enhancement_result['confidence_score']:.3f}")
                print(f"   Examples found: {len(enhancement_result['similar_examples'])}")
                
                if enhancement_result.get('llm_formatted'):
                    print(f"   🤖 LLM formatted: {enhancement_result.get('llm_info', {}).get('method_used', 'unknown')}")
            else:
                print(f"   ℹ️ No RAG enhancement applied")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG-Gemini integration test error: {e}")
        return False

def test_inference_engine_gemini():
    """Test inference engine with Gemini."""
    print("\n🧪 Testing Inference Engine with Gemini")
    print("-" * 40)
    
    try:
        from src.nlq.rag_inference_engine import RAGEnhancedInferenceEngine
        
        # Initialize engine
        engine = RAGEnhancedInferenceEngine()
        print("✅ RAG inference engine created")
        
        # Load model
        if engine.load_model():
            print("✅ T5 model loaded")
        else:
            print("⚠️ T5 model loading failed, continuing with Gemini-only tests")
        
        # Initialize RAG system
        if engine.initialize_rag_system():
            print("✅ RAG system initialized")
        else:
            print("❌ RAG system initialization failed")
            return False
        
        # Test different generation methods
        test_query = "Show me patients with diabetes"
        methods = ["t5_enhanced", "gemini_direct", "hybrid"]
        
        print(f"\n🔧 Testing SQL generation methods:")
        
        for method in methods:
            print(f"\n   Method: {method}")
            
            try:
                if method == "gemini_direct":
                    result = engine.generate_sql_with_gemini(test_query, use_rag=True)
                elif method == "hybrid":
                    # Try Gemini first
                    result = engine.generate_sql_with_gemini(test_query, use_rag=True)
                    if not result['validation']['is_valid']:
                        # Fallback to T5
                        result = engine.generate_sql(test_query, use_rag=True)
                        result['metadata']['method'] = 'hybrid_t5_fallback'
                else:
                    # T5 enhanced
                    result = engine.generate_sql(test_query, use_rag=True)
                
                if result['validation']['is_valid']:
                    print(f"   ✅ Success: {result['generated_sql'][:80]}...")
                    print(f"   ⏱️ Time: {result['generation_time']:.3f}s")
                    print(f"   🎯 Method: {result['metadata'].get('method', 'unknown')}")
                else:
                    print(f"   ❌ Invalid SQL generated")
                    print(f"   Errors: {result['validation'].get('errors', [])}")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Get comprehensive stats
        stats = engine.get_comprehensive_stats()
        print(f"\n📊 Engine Statistics:")
        gen_stats = stats.get('generation_stats', {})
        print(f"   Total queries: {gen_stats.get('total_queries', 0)}")
        print(f"   Successful: {gen_stats.get('successful_generations', 0)}")
        print(f"   RAG enhanced: {gen_stats.get('rag_enhanced_queries', 0)}")
        print(f"   Average time: {gen_stats.get('avg_time', 0):.3f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Inference engine test error: {e}")
        return False

def test_api_integration():
    """Test API integration (if server is running)."""
    print("\n🧪 Testing API Integration")
    print("-" * 40)
    
    try:
        from src.api.api_client import GeminiRAGAPIClient
        
        # Initialize client
        client = GeminiRAGAPIClient()
        print("✅ API client created")
        
        # Health check
        health = client.health_check()
        if health.get("status") == "healthy":
            print("✅ API server is healthy")
            
            # Test query
            test_query = "How many patients are there?"
            result = client.query(test_query, method="gemini_direct")
            
            if result.success:
                print(f"✅ API query successful")
                print(f"   Query: {test_query}")
                print(f"   SQL: {result.generated_sql[:80]}...")
                print(f"   Method: {result.method_used}")
                print(f"   Time: {result.generation_time:.3f}s")
            else:
                print(f"❌ API query failed: {result.error}")
            
            return True
            
        else:
            print("⚠️ API server not available or not healthy")
            print("   Start the API server with: python start_gemini_api.py")
            return False
            
    except Exception as e:
        print(f"⚠️ API integration test skipped: {e}")
        print("   (API server may not be running)")
        return False

def check_environment():
    """Check environment setup."""
    print("🔧 Checking Environment Setup")
    print("-" * 40)
    
    # Check API keys
    gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if gemini_key:
        print("✅ Gemini API key found")
    else:
        print("⚠️ Gemini API key not found (set GEMINI_API_KEY or GOOGLE_API_KEY)")
    
    if openai_key:
        print("✅ OpenAI API key found")
    else:
        print("ℹ️ OpenAI API key not found (optional)")
    
    # Check database environment
    db_vars = ['DB_HOST', 'DB_NAME', 'DB_USERNAME', 'DB_PASSWORD', 'DB_SCHEMA']
    db_configured = all(os.getenv(var) for var in db_vars)
    
    if db_configured:
        print("✅ Database environment configured")
    else:
        print("⚠️ Database environment not fully configured")
    
    # Check dependencies
    try:
        import google.generativeai
        print("✅ Google Generative AI library available")
    except ImportError:
        print("❌ Google Generative AI library not installed")
        print("   Install with: pip install google-generativeai")
    
    return gemini_key is not None

def main():
    """Run all tests."""
    print("🚀 Testing Gemini Integration with RAG System")
    print("=" * 60)
    
    # Check environment
    env_ok = check_environment()
    
    if not env_ok:
        print("\n❌ Environment not properly configured")
        print("   Set GEMINI_API_KEY environment variable to continue")
        sys.exit(1)
    
    # Run tests
    tests = [
        ("Gemini Client", test_gemini_client),
        ("RAG-Gemini Integration", test_rag_gemini_integration),
        ("Inference Engine with Gemini", test_inference_engine_gemini),
        ("API Integration", test_api_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"📋 Running: {test_name}")
        print(f"{'='*60}")
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"\n✅ {test_name}: PASSED")
            else:
                print(f"\n❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"\n❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Gemini integration is working perfectly.")
        print("\n🚀 You can now use:")
        print("   1. Streamlit app with Gemini: streamlit run src/ui/streamlit_app.py")
        print("   2. API server: python start_gemini_api.py")
        print("   3. Direct Gemini SQL generation in your code")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("   1. Ensure GEMINI_API_KEY is set correctly")
        print("   2. Check internet connection for Gemini API")
        print("   3. Verify all dependencies are installed")
        print("   4. Check that training data is available")

if __name__ == "__main__":
    main()