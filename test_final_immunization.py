#!/usr/bin/env python3
"""
Final test for the immunization query fix
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from nlq.inference_engine import ClinicalInferenceEngine

def test_immunization_query():
    """Test the immunization query"""
    print("🧪 TESTING IMMUNIZATION QUERY FIX")
    print("="*50)
    
    engine = ClinicalInferenceEngine()
    engine.load_model()
    
    query = "How many patients received more than 2 immunizations?"
    print(f"Query: '{query}'")
    
    # Test the full system
    result = engine.generate_sql(query)
    
    print(f"\nGenerated SQL: {result.get('generated_sql', 'N/A')}")
    print(f"Method used: {result.get('metadata', {}).get('method', 'Unknown')}")
    print(f"Success: {result.get('success', False)}")
    
    # Check if it's the correct SQL
    expected_pattern = "immunizations.*GROUP BY.*HAVING.*COUNT.*>"
    import re
    if re.search(expected_pattern, result.get('generated_sql', ''), re.IGNORECASE):
        print("✅ CORRECT: SQL includes immunizations table with GROUP BY and HAVING")
    else:
        print("❌ INCORRECT: SQL doesn't properly query immunizations with aggregation")
        
        # Show what the basic fallback would generate
        print(f"\n🔧 What basic fallback generates:")
        fallback_result = engine.fallback_generator.generate_sql(query)
        print(f"Fallback SQL: {fallback_result.get('generated_sql', 'N/A')}")

if __name__ == "__main__":
    test_immunization_query()