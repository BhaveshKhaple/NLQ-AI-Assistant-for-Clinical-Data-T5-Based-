#!/usr/bin/env python3
"""
Test script to debug the immunization query issue
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from nlq.inference_engine import ClinicalInferenceEngine

def test_immunization_query():
    """Test the specific immunization query that's failing"""
    print("🔍 TESTING IMMUNIZATION QUERY")
    print("="*50)
    
    engine = ClinicalInferenceEngine()
    engine.load_model()
    
    query = "How many patients received more than 2 immunizations?"
    print(f"Query: '{query}'")
    
    # Test direct T5 model
    print(f"\n1️⃣ DIRECT T5 MODEL:")
    try:
        input_text = f"translate English to SQL: {query}"
        inputs = engine.tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)
        
        import torch
        with torch.no_grad():
            outputs = engine.model.generate(
                **inputs,
                max_length=256,
                num_beams=4,
                early_stopping=True,
                do_sample=False
            )
        
        raw_t5_output = engine.tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"Raw T5: '{raw_t5_output}'")
        
        validation = engine._validate_sql(raw_t5_output)
        print(f"Valid: {validation['is_valid']}")
        if validation['errors']:
            print(f"Errors: {validation['errors']}")
            
    except Exception as e:
        print(f"❌ T5 Failed: {e}")
    
    # Test fallback generators
    print(f"\n2️⃣ BASIC FALLBACK:")
    try:
        fallback_result = engine.fallback_generator.generate_sql(query)
        print(f"SQL: '{fallback_result.get('generated_sql', 'N/A')}'")
        print(f"Method: {fallback_result.get('method', 'Unknown')}")
        print(f"Pattern: {fallback_result.get('pattern_matched', 'None')}")
    except Exception as e:
        print(f"❌ Basic Fallback Failed: {e}")
    
    print(f"\n3️⃣ INTELLIGENT FALLBACK:")
    try:
        intelligent_result = engine.intelligent_fallback.generate_sql(query)
        print(f"SQL: '{intelligent_result.get('generated_sql', 'N/A')}'")
        print(f"Method: {intelligent_result.get('method', 'Unknown')}")
        if 'intent' in intelligent_result:
            print(f"Intent: {intelligent_result['intent']}")
    except Exception as e:
        print(f"❌ Intelligent Fallback Failed: {e}")
    
    # Test full system
    print(f"\n4️⃣ FULL SYSTEM:")
    result = engine.generate_sql(query)
    print(f"Final SQL: '{result.get('generated_sql', 'N/A')}'")
    print(f"Success: {result.get('success', False)}")
    if 'metadata' in result:
        print(f"Method Used: {result['metadata'].get('method', 'Unknown')}")

def test_related_queries():
    """Test related immunization/vaccination queries"""
    print(f"\n" + "="*50)
    print("🧪 TESTING RELATED QUERIES")
    print("="*50)
    
    engine = ClinicalInferenceEngine()
    engine.load_model()
    
    related_queries = [
        "How many patients received immunizations?",
        "Show patients with more than 2 vaccines",
        "Count patients with multiple immunizations",
        "List patients who received flu vaccine",
        "How many immunizations were given?"
    ]
    
    for i, query in enumerate(related_queries, 1):
        print(f"\n--- Test {i}: '{query}' ---")
        result = engine.generate_sql(query)
        print(f"SQL: '{result.get('generated_sql', 'N/A')}'")

if __name__ == "__main__":
    test_immunization_query()
    test_related_queries()