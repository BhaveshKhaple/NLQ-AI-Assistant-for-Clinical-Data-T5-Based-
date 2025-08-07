#!/usr/bin/env python3
"""
RAG System Demonstration
Interactive demonstration of the RAG-enhanced Clinical NLQ system.
"""

import sys
import time
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))

from src.nlq.rag_enhanced_nlq import RAGEnhancedNLQ

def print_header():
    """Print demonstration header."""
    print("🤖 RAG-Enhanced Clinical NLQ System Demo")
    print("=" * 60)
    print("This demo shows how RAG improves query processing by:")
    print("• Finding similar examples from training data")
    print("• Enhancing queries based on successful patterns")
    print("• Providing confidence scores for enhancements")
    print("=" * 60)
    print()

def demo_rag_enhancement():
    """Demonstrate RAG query enhancement."""
    print("🔧 Initializing RAG system...")
    rag_system = RAGEnhancedNLQ()
    
    if not rag_system.load_training_data():
        print("❌ Failed to load training data")
        return
    
    print("✅ RAG system ready!")
    print(f"📚 Loaded {len(rag_system.training_data)} training examples")
    print()
    
    # Demo queries with different complexity levels
    demo_queries = [
        {
            "query": "How many patients are there?",
            "description": "Simple count query"
        },
        {
            "query": "Show me diabetic patients",
            "description": "Basic filter with medical condition"
        },
        {
            "query": "Find high cost patients",
            "description": "Financial analysis query"
        },
        {
            "query": "List medications for heart problems",
            "description": "Complex medical query"
        },
        {
            "query": "What doctors are in Boston?",
            "description": "Location-based provider query"
        }
    ]
    
    print("🧪 Testing RAG Enhancement on Sample Queries")
    print("-" * 60)
    
    for i, demo in enumerate(demo_queries, 1):
        print(f"\n{i}. {demo['description']}")
        print(f"   Query: \"{demo['query']}\"")
        print("   " + "-" * 50)
        
        # Process with RAG
        start_time = time.time()
        result = rag_system.enhance_query(demo['query'])
        processing_time = time.time() - start_time
        
        # Display results
        print(f"   ✨ Enhanced: \"{result['enhanced_query']}\"")
        print(f"   🎯 Method: {result['method_used'].replace('_', ' ').title()}")
        print(f"   📊 Confidence: {result['confidence_score']:.3f}")
        print(f"   ⏱️  Time: {processing_time:.3f}s")
        
        # Show similar examples
        if result['similar_examples']:
            print(f"   📚 Found {len(result['similar_examples'])} similar examples:")
            for j, example in enumerate(result['similar_examples'][:2], 1):
                similarity = example['similarity_score']
                query_text = example['extracted_nlq']
                print(f"      {j}. \"{query_text}\" (similarity: {similarity:.3f})")
        
        # Show enhancement effect
        if result['enhanced_query'] != result['original_query']:
            print("   🔄 Query was enhanced based on training patterns!")
        else:
            print("   ℹ️  Query used as-is (no enhancement needed)")
    
    print(f"\n📊 Session Statistics:")
    stats = rag_system.get_stats()
    print(f"   Total Queries: {stats['total_queries']}")
    print(f"   RAG Enhanced: {stats['rag_enhanced_queries']}")
    print(f"   Enhancement Rate: {stats.get('rag_enhancement_rate', 0)*100:.1f}%")
    print(f"   Average Time: {stats.get('avg_total_time', 0):.3f}s")

def demo_similarity_search():
    """Demonstrate similarity search capabilities."""
    print("\n🔍 Similarity Search Demonstration")
    print("-" * 60)
    
    rag_system = RAGEnhancedNLQ()
    if not rag_system.load_training_data():
        return
    
    test_query = "How many patients with heart disease?"
    print(f"🎯 Test Query: \"{test_query}\"")
    print("\n📚 Most Similar Training Examples:")
    
    similar_examples = rag_system.retrieve_similar_examples(test_query, top_k=5)
    
    for i, example in enumerate(similar_examples, 1):
        similarity = example['similarity_score']
        query_text = example['extracted_nlq']
        sql_text = example['target_text']
        
        print(f"\n{i}. Similarity: {similarity:.3f}")
        print(f"   Query: \"{query_text}\"")
        print(f"   SQL: {sql_text[:80]}{'...' if len(sql_text) > 80 else ''}")

def interactive_demo():
    """Interactive RAG demonstration."""
    print("\n💬 Interactive RAG Demo")
    print("-" * 60)
    print("Enter your own queries to see RAG enhancement in action!")
    print("Type 'quit' to exit")
    print()
    
    rag_system = RAGEnhancedNLQ()
    if not rag_system.load_training_data():
        return
    
    while True:
        try:
            user_query = input("🔍 Enter your query: ").strip()
            
            if user_query.lower() in ['quit', 'exit', 'q']:
                print("👋 Thanks for trying the RAG demo!")
                break
            
            if not user_query:
                continue
            
            print("   Processing...")
            result = rag_system.enhance_query(user_query)
            
            print(f"   ✨ Enhanced: \"{result['enhanced_query']}\"")
            print(f"   📊 Confidence: {result['confidence_score']:.3f}")
            print(f"   🎯 Method: {result['method_used'].replace('_', ' ').title()}")
            
            if result['similar_examples']:
                print(f"   📚 Top similar example:")
                top_example = result['similar_examples'][0]
                print(f"      \"{top_example['extracted_nlq']}\" (sim: {top_example['similarity_score']:.3f})")
            
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Demo interrupted by user")
            break
        except Exception as e:
            print(f"   ❌ Error: {e}")

def main():
    """Main demonstration function."""
    print_header()
    
    try:
        # Basic RAG enhancement demo
        demo_rag_enhancement()
        
        # Similarity search demo
        demo_similarity_search()
        
        # Interactive demo
        interactive_demo()
        
    except KeyboardInterrupt:
        print("\n👋 Demo stopped by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure dependencies are installed: pip install sentence-transformers scikit-learn")
        print("   2. Check that training data exists: data/processed/final_merged_dataset/train_data.json")
        print("   3. Verify Python path includes src directory")

if __name__ == "__main__":
    main()