#!/usr/bin/env python3
"""
Test RAG Integration in Original Streamlit App
Quick test to verify RAG functionality is working in the updated original app.
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))

def test_rag_imports():
    """Test that RAG components can be imported."""
    print("🧪 Testing RAG imports...")
    
    try:
        from src.nlq.rag_inference_engine import RAGEnhancedInferenceEngine
        print("✅ RAGEnhancedInferenceEngine imported successfully")
        
        from src.nlq.rag_enhanced_nlq import RAGEnhancedNLQ
        print("✅ RAGEnhancedNLQ imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_rag_initialization():
    """Test RAG system initialization."""
    print("\n🧪 Testing RAG initialization...")
    
    try:
        from src.nlq.rag_inference_engine import RAGEnhancedInferenceEngine
        
        # Initialize engine
        engine = RAGEnhancedInferenceEngine()
        print("✅ RAG engine created")
        
        # Test model loading (this might take time)
        print("📥 Testing model loading...")
        if engine.load_model():
            print("✅ Model loaded successfully")
            
            # Test RAG system initialization
            print("🔧 Testing RAG system initialization...")
            if engine.initialize_rag_system():
                print("✅ RAG system initialized successfully")
                
                # Get stats
                stats = engine.get_comprehensive_stats()
                print(f"📊 Training examples loaded: {stats.get('training_examples', 0)}")
                return True
            else:
                print("⚠️ RAG system initialization failed")
                return False
        else:
            print("⚠️ Model loading failed")
            return False
            
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return False

def test_streamlit_app_imports():
    """Test that the updated Streamlit app can import RAG components."""
    print("\n🧪 Testing Streamlit app RAG integration...")
    
    try:
        # Import the updated app
        sys.path.append(str(Path(__file__).parent / "src" / "ui"))
        from streamlit_app import ClinicalNLQApp
        print("✅ Updated Streamlit app imported successfully")
        
        # Test that it has RAG methods
        app = ClinicalNLQApp()
        
        # Check if RAG methods exist
        if hasattr(app, '_get_rag_engine'):
            print("✅ RAG engine method found")
        else:
            print("❌ RAG engine method missing")
            return False
            
        if hasattr(app, '_initialize_rag_engine'):
            print("✅ RAG initialization method found")
        else:
            print("❌ RAG initialization method missing")
            return False
        
        print("✅ Streamlit app RAG integration verified")
        return True
        
    except Exception as e:
        print(f"❌ Streamlit app test error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing RAG Integration in Original Streamlit App")
    print("=" * 60)
    
    tests = [
        ("RAG Imports", test_rag_imports),
        ("RAG Initialization", test_rag_initialization),
        ("Streamlit App Integration", test_streamlit_app_imports)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 40)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
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
        print("🎉 All tests passed! RAG integration is working in the original Streamlit app.")
        print("\n🚀 You can now run the original app with RAG enhancement:")
        print("   streamlit run src/ui/streamlit_app.py")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure all dependencies are installed")
        print("   2. Check that model files exist")
        print("   3. Verify training data is available")

if __name__ == "__main__":
    main()