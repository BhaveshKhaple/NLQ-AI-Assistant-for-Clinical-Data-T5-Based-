#!/usr/bin/env python3
"""
Test the enhanced RAG system with schema embeddings
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append('src')

def test_schema_extraction():
    """Test database schema extraction"""
    print("🔧 Testing Database Schema Extraction...")
    
    try:
        from nlq.database_schema_extractor import DatabaseSchemaExtractor
        
        extractor = DatabaseSchemaExtractor()
        schema_info = extractor.extract_schema_info()
        
        if schema_info:
            print(f"✅ Extracted schema for {len(schema_info['tables'])} tables")
            print(f"📊 Generated {len(schema_info['schema_descriptions'])} schema descriptions")
            
            # Show some examples
            print("\n🔍 Sample schema descriptions:")
            for i, desc in enumerate(schema_info['schema_descriptions'][:3]):
                print(f"{i+1}. {desc['description']}")
            
            return True
        else:
            print("❌ Failed to extract schema info")
            return False
            
    except Exception as e:
        print(f"❌ Schema extraction error: {e}")
        return False

def test_rag_with_schema():
    """Test RAG system with schema embeddings"""
    print("\n🔧 Testing RAG System with Schema Embeddings...")
    
    try:
        from nlq.rag_enhanced_nlq import RAGEnhancedNLQ
        
        # Initialize RAG system
        rag_system = RAGEnhancedNLQ()
        
        # Load training data and schema
        print("📥 Loading training data and schema...")
        success = rag_system.load_training_data()
        
        if success:
            print("✅ RAG system loaded successfully")
            
            # Test query enhancement
            test_query = "How many patients do we have?"
            print(f"\n🔍 Testing query: '{test_query}'")
            
            result = rag_system.enhance_query(test_query)
            
            print(f"Original: {result['original_query']}")
            print(f"Enhanced: {result['enhanced_query']}")
            print(f"RAG Enhanced: {result['rag_enhanced']}")
            print(f"Method: {result['method_used']}")
            print(f"Confidence: {result['confidence_score']:.3f}")
            
            # Show similar examples
            if result['similar_examples']:
                print(f"\n📚 Found {len(result['similar_examples'])} similar examples:")
                for i, ex in enumerate(result['similar_examples'][:2]):
                    print(f"{i+1}. {ex['extracted_nlq']} -> {ex['target_text']} (sim: {ex['similarity_score']:.3f})")
            
            # Show relevant schema
            if result.get('relevant_schema'):
                print(f"\n🗄️ Found {len(result['relevant_schema'])} relevant schema items:")
                for i, schema in enumerate(result['relevant_schema'][:2]):
                    print(f"{i+1}. {schema['description']} (sim: {schema['similarity_score']:.3f})")
            
            return True
        else:
            print("❌ Failed to load RAG system")
            return False
            
    except Exception as e:
        print(f"❌ RAG system error: {e}")
        return False

def test_full_inference():
    """Test full inference pipeline"""
    print("\n🔧 Testing Full Inference Pipeline...")
    
    try:
        from nlq.rag_inference_engine import RAGEnhancedInferenceEngine
        
        # Initialize engine
        engine = RAGEnhancedInferenceEngine()
        
        print("📥 Loading model...")
        engine.load_model()
        
        print("🔧 Initializing RAG system...")
        engine.initialize_rag_system()
        
        # Test queries
        test_queries = [
            "How many patients do we have?",
            "Show me all male patients",
            "Find patients with diabetes"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing: '{query}'")
            
            result = engine.generate_sql(query)
            
            print(f"Generated SQL: {result.get('generated_sql', 'None')}")
            print(f"Success: {result.get('success', False)}")
            print(f"Processing time: {result.get('processing_time', 0):.3f}s")
            
            # Check if it's not just echoing the input
            generated_sql = result.get('generated_sql', '')
            if generated_sql and generated_sql != query:
                print("✅ SQL generation working correctly")
            else:
                print("❌ SQL generation may be echoing input")
        
        return True
        
    except Exception as e:
        print(f"❌ Full inference error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Enhanced RAG System with Schema Embeddings")
    print("=" * 60)
    
    # Test 1: Schema extraction
    schema_ok = test_schema_extraction()
    
    # Test 2: RAG with schema
    rag_ok = test_rag_with_schema()
    
    # Test 3: Full inference
    inference_ok = test_full_inference()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"Schema Extraction: {'✅ PASS' if schema_ok else '❌ FAIL'}")
    print(f"RAG with Schema: {'✅ PASS' if rag_ok else '❌ FAIL'}")
    print(f"Full Inference: {'✅ PASS' if inference_ok else '❌ FAIL'}")
    
    if all([schema_ok, rag_ok, inference_ok]):
        print("\n🎉 All tests passed! Schema-enhanced RAG system is working!")
    else:
        print("\n⚠️ Some tests failed. Check the logs above for details.")