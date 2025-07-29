#!/usr/bin/env python3
"""
Example Inference Usage
Simple example demonstrating how to use the Phase 5 inference pipeline.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.nlq.inference_pipeline import create_pipeline

def simple_example():
    """Simple example of using the inference pipeline."""
    print("🏥 Clinical NLQ Inference Pipeline - Simple Example")
    print("=" * 55)
    
    # Set database password if not already set
    if not os.getenv('DB_PASSWORD'):
        print("⚠️ Setting empty DB_PASSWORD for demo")
        os.environ['DB_PASSWORD'] = ''
    
    # Create and initialize pipeline
    print("🚀 Initializing pipeline...")
    pipeline = create_pipeline()
    
    if not pipeline.is_initialized:
        print("❌ Pipeline initialization failed!")
        return
    
    print("✅ Pipeline initialized successfully!")
    
    # Example queries
    example_queries = [
        "How many patients do we have?",
        "Show me all male patients",
        "Find patients with diabetes",
        "What are the most common medical conditions?",
        "List all healthcare organizations"
    ]
    
    print(f"\n📝 Processing {len(example_queries)} example queries...")
    
    for i, query in enumerate(example_queries, 1):
        print(f"\n🔍 Query {i}: {query}")
        print("-" * 40)
        
        # Process the query
        result = pipeline.process_query(
            nlq=query,
            output_formats=['table', 'json'],  # Get both table and JSON formats
            user_id='demo_user'
        )
        
        if result['success']:
            # Query was successful
            metadata = result['metadata']
            print(f"✅ Success!")
            print(f"   Generated SQL: {result['generated_sql']}")
            print(f"   Rows returned: {metadata['rows_returned']}")
            print(f"   Processing time: {metadata['total_time']:.3f} seconds")
            
            # Show sample data from table format
            table_result = result['results']['formats']['table']
            if table_result['success'] and table_result['data']:
                print(f"   Sample data (first 3 rows):")
                for j, row in enumerate(table_result['data'][:3], 1):
                    print(f"     Row {j}: {row}")
            
            # Show JSON size
            json_result = result['results']['formats']['json']
            if json_result['success']:
                print(f"   JSON output size: {json_result['size_bytes']} bytes")
        
        else:
            # Query failed
            print(f"❌ Failed!")
            print(f"   Error: {result['error']}")
            print(f"   Error type: {result.get('error_type', 'Unknown')}")
            
            # Show generated SQL if available (for debugging)
            if 'generated_sql' in result:
                print(f"   Generated SQL: {result['generated_sql']}")
    
    # Show pipeline statistics
    print(f"\n📊 Pipeline Statistics:")
    status = pipeline.get_pipeline_status()
    stats = status['pipeline_stats']
    
    print(f"   Total queries: {stats['total_queries']}")
    print(f"   Successful: {stats['successful_queries']}")
    print(f"   Failed: {stats['failed_queries']}")
    
    if stats['total_queries'] > 0:
        success_rate = stats['successful_queries'] / stats['total_queries']
        print(f"   Success rate: {success_rate:.1%}")
        print(f"   Average processing time: {stats['avg_total_time']:.3f}s")
    
    # Close pipeline
    print(f"\n🔚 Closing pipeline...")
    pipeline.close()
    print(f"✅ Done!")

def advanced_example():
    """Advanced example with custom parameters."""
    print("\n🏥 Clinical NLQ Inference Pipeline - Advanced Example")
    print("=" * 58)
    
    # Create pipeline
    pipeline = create_pipeline()
    
    if not pipeline.is_initialized:
        print("❌ Pipeline initialization failed!")
        return
    
    # Advanced query with custom parameters
    query = "Find elderly patients with multiple chronic conditions"
    
    print(f"🔍 Advanced Query: {query}")
    print("-" * 50)
    
    # Process with custom parameters
    result = pipeline.process_query(
        nlq=query,
        output_formats=['table', 'json', 'csv', 'summary'],  # Multiple formats
        user_id='advanced_user',
        session_info={'demo_type': 'advanced', 'timestamp': '2024-01-01'},
        generation_params={
            'num_beams': 8,  # More thorough search
            'temperature': 0.7,
            'do_sample': True,
            'include_schema_context': True
        },
        execution_params={
            'timeout': 60,  # Longer timeout
            'max_rows': 100  # More rows
        },
        format_params={
            'include_metadata': True
        }
    )
    
    if result['success']:
        print(f"✅ Advanced query successful!")
        
        # Show detailed metadata
        metadata = result['metadata']
        print(f"\n📊 Detailed Timing:")
        print(f"   SQL Generation: {metadata['generation_time']:.3f}s")
        print(f"   Database Execution: {metadata['execution_time']:.3f}s")
        print(f"   Result Formatting: {metadata['formatting_time']:.3f}s")
        print(f"   Total Time: {metadata['total_time']:.3f}s")
        
        print(f"\n📋 Results:")
        print(f"   Rows returned: {metadata['rows_returned']}")
        print(f"   Truncated: {metadata['truncated']}")
        
        # Show format results
        formats = result['results']['formats']
        print(f"\n🎨 Format Results:")
        for format_name, format_result in formats.items():
            if format_result['success']:
                print(f"   ✅ {format_name.upper()}: Success")
                if format_name == 'summary':
                    summary = format_result['summary']
                    print(f"      Data types: {len(summary.get('data_types', {}))}")
                    print(f"      Memory usage: {summary.get('memory_usage_mb', 0):.2f} MB")
            else:
                print(f"   ❌ {format_name.upper()}: {format_result['error']}")
        
        # Show generation details
        gen_details = result['generation_details']
        validation = gen_details['validation']
        print(f"\n🧠 Generation Details:")
        print(f"   SQL valid: {validation['is_valid']}")
        print(f"   Has schema prefix: {validation['has_schema_prefix']}")
        print(f"   SQL length: {validation['sql_length']} characters")
        
        if validation['warnings']:
            print(f"   Warnings: {validation['warnings']}")
    
    else:
        print(f"❌ Advanced query failed: {result['error']}")
    
    # Batch processing example
    print(f"\n📦 Batch Processing Example:")
    batch_queries = [
        "How many patients are over 65?",
        "What percentage of patients are diabetic?",
        "Which provider sees the most patients?"
    ]
    
    batch_result = pipeline.batch_process(
        batch_queries,
        output_formats=['table'],
        user_id='batch_user'
    )
    
    if batch_result['success']:
        print(f"✅ Batch processing successful!")
        print(f"   Queries processed: {batch_result['batch_size']}")
        print(f"   Success rate: {batch_result['success_rate']:.1%}")
        print(f"   Total time: {batch_result['total_batch_time']:.3f}s")
        print(f"   Average per query: {batch_result['avg_query_time']:.3f}s")
    else:
        print(f"❌ Batch processing failed: {batch_result.get('error', 'Unknown error')}")
    
    # Close pipeline
    pipeline.close()

def main():
    """Main function."""
    try:
        # Run simple example
        simple_example()
        
        # Run advanced example
        advanced_example()
        
        print(f"\n🎉 All examples completed successfully!")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()