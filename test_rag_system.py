#!/usr/bin/env python3
"""
Test RAG-Enhanced NLQ System
Comprehensive testing of the RAG-enhanced inference engine.
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))

from src.nlq.rag_inference_engine import RAGEnhancedInferenceEngine

def test_rag_system():
    """Test the RAG-enhanced system comprehensively."""
    print("🚀 Testing RAG-Enhanced NLQ System")
    print("=" * 60)
    
    # Initialize the engine
    print("🔧 Initializing RAG-Enhanced Inference Engine...")
    engine = RAGEnhancedInferenceEngine()
    
    # Load model
    print("📥 Loading T5 model...")
    if not engine.load_model():
        print("❌ Failed to load model. Exiting.")
        return
    
    # Initialize RAG system
    print("🔍 Initializing RAG system...")
    if not engine.initialize_rag_system():
        print("⚠️ RAG system not available, testing traditional approach only")
    
    # Test queries - mix of simple and complex
    test_queries = [
        # Simple queries
        "How many patients do we have?",
        "Show me all male patients",
        "List all medications",
        
        # Medium complexity
        "Find patients with diabetes",
        "Show high-cost patients",
        "List providers in Boston",
        
        # Complex queries
        "Find patients with both diabetes and hypertension",
        "Show patients on multiple medications",
        "What are the most common conditions?",
        "List patients with recent visits"
    ]
    
    print(f"\n🧪 Testing {len(test_queries)} queries")
    print("-" * 60)
    
    results = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Testing: {query}")
        print("-" * 40)
        
        # Test with RAG enhancement
        start_time = time.time()
        result = engine.generate_sql(query, use_rag=True)
        total_time = time.time() - start_time
        
        results.append({
            'query': query,
            'result': result,
            'total_time': total_time
        })
        
        # Display results
        print(f"   Original Query: {result['nlq']}")
        if result['processed_nlq'] != result['nlq']:
            print(f"   Processed Query: {result['processed_nlq']}")
        
        print(f"   Generated SQL: {result['generated_sql']}")
        print(f"   Method: {result['metadata']['method']}")
        print(f"   Valid: {'✅' if result['validation']['is_valid'] else '❌'}")
        print(f"   Generation Time: {result['generation_time']:.3f}s")
        print(f"   Total Time: {total_time:.3f}s")
        
        # RAG information
        if result['metadata'].get('rag_enhanced'):
            rag_info = result['metadata']['rag_info']
            print(f"   RAG Enhanced: ✅")
            print(f"   RAG Method: {rag_info['method_used']}")
            print(f"   RAG Confidence: {rag_info['confidence_score']:.3f}")
            if rag_info['similar_examples']:
                print(f"   Similar Examples: {len(rag_info['similar_examples'])}")
        else:
            print(f"   RAG Enhanced: ❌")
        
        # Validation details
        if not result['validation']['is_valid']:
            print(f"   Errors: {', '.join(result['validation']['errors'])}")
        
        if result['validation'].get('warnings'):
            print(f"   Warnings: {', '.join(result['validation']['warnings'])}")
    
    # Summary statistics
    print(f"\n📊 SUMMARY STATISTICS")
    print("=" * 60)
    
    total_queries = len(results)
    valid_queries = sum(1 for r in results if r['result']['validation']['is_valid'])
    rag_enhanced = sum(1 for r in results if r['result']['metadata'].get('rag_enhanced'))
    avg_generation_time = sum(r['result']['generation_time'] for r in results) / total_queries
    avg_total_time = sum(r['total_time'] for r in results) / total_queries
    
    print(f"Total Queries: {total_queries}")
    print(f"Valid SQL Generated: {valid_queries}/{total_queries} ({valid_queries/total_queries*100:.1f}%)")
    print(f"RAG Enhanced Queries: {rag_enhanced}/{total_queries} ({rag_enhanced/total_queries*100:.1f}%)")
    print(f"Average Generation Time: {avg_generation_time:.3f}s")
    print(f"Average Total Time: {avg_total_time:.3f}s")
    
    # Engine statistics
    engine_stats = engine.get_comprehensive_stats()
    print(f"\n🔧 ENGINE STATISTICS")
    print("-" * 30)
    gen_stats = engine_stats['generation_stats']
    print(f"Success Rate: {gen_stats['successful_generations']}/{gen_stats['total_queries']} ({gen_stats['successful_generations']/gen_stats['total_queries']*100:.1f}%)")
    
    if engine.rag_enabled and 'rag_stats' in engine_stats['generation_stats']:
        rag_stats = engine_stats['generation_stats']['rag_stats']
        print(f"RAG Enhancement Rate: {gen_stats.get('rag_enhancement_rate', 0)*100:.1f}%")
        print(f"RAG Improvement Rate: {gen_stats.get('rag_improvement_rate', 0)*100:.1f}%")
    
    # Performance assessment
    print(f"\n🎯 PERFORMANCE ASSESSMENT")
    print("-" * 30)
    
    if valid_queries == total_queries:
        print("✅ EXCELLENT - All queries generated valid SQL!")
    elif valid_queries >= total_queries * 0.9:
        print("✅ VERY GOOD - 90%+ queries successful")
    elif valid_queries >= total_queries * 0.8:
        print("✅ GOOD - 80%+ queries successful")
    elif valid_queries >= total_queries * 0.7:
        print("⚠️ MODERATE - 70%+ queries successful, room for improvement")
    else:
        print("❌ NEEDS IMPROVEMENT - Less than 70% success rate")
    
    # Time performance
    if avg_generation_time < 2.0:
        print("🚀 FAST - Average generation time < 2s")
    elif avg_generation_time < 5.0:
        print("⚡ MODERATE - Average generation time < 5s")
    else:
        print("🐌 SLOW - Average generation time > 5s")
    
    # Save detailed results
    report = {
        'timestamp': datetime.now().isoformat(),
        'test_summary': {
            'total_queries': total_queries,
            'valid_queries': valid_queries,
            'rag_enhanced': rag_enhanced,
            'success_rate': valid_queries / total_queries,
            'rag_enhancement_rate': rag_enhanced / total_queries,
            'avg_generation_time': avg_generation_time,
            'avg_total_time': avg_total_time
        },
        'engine_stats': engine_stats,
        'detailed_results': [
            {
                'query': r['query'],
                'generated_sql': r['result']['generated_sql'],
                'valid': r['result']['validation']['is_valid'],
                'method': r['result']['metadata']['method'],
                'rag_enhanced': r['result']['metadata'].get('rag_enhanced', False),
                'generation_time': r['result']['generation_time'],
                'total_time': r['total_time'],
                'errors': r['result']['validation'].get('errors', []),
                'warnings': r['result']['validation'].get('warnings', [])
            }
            for r in results
        ]
    }
    
    report_file = f"RAG_SYSTEM_TEST_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    # Benchmark comparison if RAG is available
    if engine.rag_enabled:
        print(f"\n⚡ RUNNING RAG vs TRADITIONAL BENCHMARK")
        print("-" * 50)
        
        benchmark_queries = test_queries[:5]  # Use first 5 queries for benchmark
        comparison = engine.benchmark_rag_vs_traditional(benchmark_queries)
        
        print(f"Traditional Approach:")
        print(f"  Valid: {comparison['traditional_results']['valid_queries']}/{comparison['traditional_results']['total_queries']}")
        print(f"  Success Rate: {comparison['traditional_results']['validity_rate']*100:.1f}%")
        print(f"  Avg Time: {comparison['traditional_results']['avg_time']:.3f}s")
        
        print(f"RAG-Enhanced Approach:")
        print(f"  Valid: {comparison['rag_results']['valid_queries']}/{comparison['rag_results']['total_queries']}")
        print(f"  Success Rate: {comparison['rag_results']['validity_rate']*100:.1f}%")
        print(f"  Avg Time: {comparison['rag_results']['avg_time']:.3f}s")
        
        print(f"Improvement:")
        print(f"  Validity: {comparison['improvement']['validity_improvement']*100:+.1f}%")
        print(f"  Time: {comparison['improvement']['time_difference']:+.3f}s")
        print(f"  Better Results: {'✅' if comparison['improvement']['better_results'] else '❌'}")
    
    print(f"\n✅ RAG System Testing Complete!")

def test_rag_only():
    """Test just the RAG system without the full inference engine."""
    print("🔍 Testing RAG System Only")
    print("=" * 40)
    
    sys.path.append(str(Path(__file__).parent / "src"))
    from src.nlq.rag_enhanced_nlq import RAGEnhancedNLQ
    
    rag_system = RAGEnhancedNLQ()
    
    if not rag_system.load_training_data():
        print("❌ Failed to load training data")
        return
    
    test_queries = [
        "How many patients are there?",
        "Show me diabetic patients", 
        "List medications for hypertension",
        "Find high cost patients",
        "What providers are in Boston?"
    ]
    
    print(f"\n🧪 Testing {len(test_queries)} queries with RAG")
    print("-" * 40)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: {query}")
        result = rag_system.enhance_query(query)
        
        print(f"   Enhanced: {result['enhanced_query']}")
        print(f"   Method: {result['method_used']}")
        print(f"   Confidence: {result['confidence_score']:.3f}")
        print(f"   Time: {result['processing_time']:.3f}s")
        
        if result['similar_examples']:
            print(f"   Similar examples: {len(result['similar_examples'])}")
            for j, ex in enumerate(result['similar_examples'][:2], 1):
                print(f"     {j}. {ex['extracted_nlq']} (sim: {ex['similarity_score']:.3f})")
    
    print(f"\n📊 RAG Statistics:")
    stats = rag_system.get_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.3f}")
        else:
            print(f"   {key}: {value}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test RAG-Enhanced NLQ System")
    parser.add_argument("--rag-only", action="store_true", help="Test only RAG system without T5 model")
    args = parser.parse_args()
    
    if args.rag_only:
        test_rag_only()
    else:
        test_rag_system()