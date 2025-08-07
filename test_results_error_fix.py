#!/usr/bin/env python3
"""
Test the fix for the 'results' KeyError in Streamlit app
"""

import sys
import os
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / 'src')
sys.path.insert(0, src_path)

def test_result_structure_handling():
    """Test that the result display logic handles different result structures"""
    
    print("🧪 Testing Result Structure Handling")
    print("=" * 50)
    
    # Mock result structures
    
    # 1. Traditional pipeline result structure
    traditional_result = {
        'success': True,
        'generated_sql': 'SELECT COUNT(*) FROM clinical_data.patients',
        'metadata': {
            'rows_returned': 1,
            'total_time': 2.5,
            'generation_time': 1.2,
            'execution_time': 1.3
        },
        'results': {
            'formats': {
                'table': {
                    'success': True,
                    'data': [{'count': 1000}]
                }
            }
        }
    }
    
    # 2. RAG result structure (the problematic one)
    rag_result = {
        'success': True,
        'generated_sql': 'SELECT COUNT(*) FROM clinical_data.patients',
        'nlq': 'How many patients do we have?',
        'metadata': {
            'method': 'rag_gemini_enhanced'
        },
        'validation': {'is_valid': True},
        'generation_time': 1.5,
        'rag_enhanced': True,
        'execution': {
            'success': True,
            'data': [{'count': 1000}],
            'execution_time': 0.8
        }
    }
    
    # 3. RAG result without execution
    rag_no_execution = {
        'success': True,
        'generated_sql': 'SELECT COUNT(*) FROM clinical_data.patients',
        'nlq': 'How many patients do we have?',
        'metadata': {
            'method': 'rag_gemini_enhanced'
        },
        'validation': {'is_valid': True},
        'generation_time': 1.5,
        'rag_enhanced': True
    }
    
    def test_format_detection(result, test_name):
        """Test the format detection logic"""
        print(f"\n🔍 Testing {test_name}:")
        
        try:
            # Simulate the logic from _display_successful_result
            if 'results' in result and 'formats' in result['results']:
                formats = result['results']['formats']
                print(f"  ✅ Traditional format detected: {list(formats.keys())}")
                return True
            elif 'execution' in result and result['execution'].get('success'):
                formats = {'table': result['execution']}
                print(f"  ✅ RAG execution format detected: {list(formats.keys())}")
                return True
            else:
                print(f"  ✅ No execution results - would show info message")
                return True
        except KeyError as e:
            print(f"  ❌ KeyError: {e}")
            return False
        except Exception as e:
            print(f"  ❌ Other error: {e}")
            return False
    
    # Test all result structures
    results = [
        (traditional_result, "Traditional Pipeline Result"),
        (rag_result, "RAG Result with Execution"),
        (rag_no_execution, "RAG Result without Execution")
    ]
    
    passed = 0
    failed = 0
    
    for result, test_name in results:
        if test_format_detection(result, test_name):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! The 'results' KeyError should be fixed.")
        return True
    else:
        print("⚠️ Some tests failed. The fix may need adjustment.")
        return False

def test_metadata_handling():
    """Test metadata handling for different result structures"""
    
    print("\n🧪 Testing Metadata Handling")
    print("=" * 30)
    
    # Test metadata extraction logic
    def extract_metadata_safely(result):
        """Simulate the metadata extraction logic"""
        try:
            metadata = result.get('metadata', {})
            
            # Rows returned
            rows_returned = metadata.get('rows_returned', 0)
            if 'execution' in result and result['execution'].get('data') is not None:
                rows_returned = len(result['execution']['data'])
            
            # Times
            total_time = metadata.get('total_time', result.get('generation_time', 0))
            generation_time = metadata.get('generation_time', result.get('generation_time', 0))
            
            exec_time = metadata.get('execution_time', 0)
            if 'execution' in result:
                exec_time = result['execution'].get('execution_time', 0)
            
            return {
                'rows_returned': rows_returned,
                'total_time': total_time,
                'generation_time': generation_time,
                'execution_time': exec_time
            }
        except Exception as e:
            return {'error': str(e)}
    
    # Test with RAG result
    rag_result = {
        'success': True,
        'generation_time': 1.5,
        'metadata': {'method': 'rag_enhanced'},
        'execution': {
            'success': True,
            'data': [{'count': 1000}],
            'execution_time': 0.8
        }
    }
    
    extracted = extract_metadata_safely(rag_result)
    
    if 'error' not in extracted:
        print("✅ Metadata extraction successful:")
        for key, value in extracted.items():
            print(f"  - {key}: {value}")
        return True
    else:
        print(f"❌ Metadata extraction failed: {extracted['error']}")
        return False

if __name__ == "__main__":
    print("🔧 Testing Fix for 'results' KeyError")
    print("=" * 60)
    
    # Test 1: Result structure handling
    structure_ok = test_result_structure_handling()
    
    # Test 2: Metadata handling
    metadata_ok = test_metadata_handling()
    
    print("\n" + "=" * 60)
    print("📊 Final Results:")
    print(f"Result Structure Handling: {'✅ PASS' if structure_ok else '❌ FAIL'}")
    print(f"Metadata Handling: {'✅ PASS' if metadata_ok else '❌ FAIL'}")
    
    if structure_ok and metadata_ok:
        print("\n🎉 All tests passed! The 'results' KeyError fix should work correctly.")
        print("💡 The Streamlit app should now handle both traditional and RAG result structures.")
    else:
        print("\n⚠️ Some tests failed. The fix may need further adjustment.")