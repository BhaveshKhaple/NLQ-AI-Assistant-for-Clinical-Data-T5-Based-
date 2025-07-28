#!/usr/bin/env python3
"""
Debug script to test individual queries and understand model behavior
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from models.quick_model_test import QuickClinicalT5Tester

def main():
    print("🔍 Debug Model Testing")
    print("=" * 50)
    
    # Initialize tester
    tester = QuickClinicalT5Tester()
    
    # Load model
    if not tester.load_model():
        print("❌ Failed to load model. Exiting.")
        return
    
    # Test individual queries with different parameters
    test_queries = [
        "How many patients do we have?",
        "SELECT COUNT(*) FROM clinical_data.patients",
        "Show all patients",
        "Find patients with diabetes"
    ]
    
    print("\n🧪 Testing individual queries with different generation parameters:")
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        
        # Test with different beam sizes
        for num_beams in [1, 2, 4]:
            for max_length in [128, 256]:
                try:
                    result = tester.generate_sql(query, max_length=max_length, num_beams=num_beams)
                    print(f"  Beams={num_beams}, MaxLen={max_length}: {result}")
                except Exception as e:
                    print(f"  Beams={num_beams}, MaxLen={max_length}: ERROR - {e}")
    
    # Test with raw model input format
    print("\n🔧 Testing with raw model input format:")
    raw_inputs = [
        "translate to sql: How many patients do we have?",
        "translate to sql: Show all patients",
        "translate to sql: Find patients with diabetes"
    ]
    
    for raw_input in raw_inputs:
        try:
            # Direct tokenization and generation
            inputs = tester.tokenizer(
                raw_input,
                return_tensors="pt",
                max_length=256,
                truncation=True,
                padding=True
            ).to(tester.device)
            
            with tester.model.eval():
                outputs = tester.model.generate(
                    **inputs,
                    max_length=128,
                    num_beams=1,
                    early_stopping=True,
                    pad_token_id=tester.tokenizer.pad_token_id,
                    eos_token_id=tester.tokenizer.eos_token_id,
                    do_sample=False
                )
            
            result = tester.tokenizer.decode(outputs[0], skip_special_tokens=True)
            print(f"  Raw input: {raw_input}")
            print(f"  Result: {result}")
            
        except Exception as e:
            print(f"  Raw input: {raw_input}")
            print(f"  ERROR: {e}")

if __name__ == "__main__":
    main()