#!/usr/bin/env python3
"""
Quick Test for Final Model 2nd Run
Fast evaluation with just a few key examples
"""

import json
import torch
import time
from transformers import T5ForConditionalGeneration, AutoTokenizer
from datetime import datetime

def quick_test_model():
    print("🚀 Quick Test - Final Model 2nd Run")
    print("=" * 50)
    
    # Model path
    model_path = "d:/projects/healthca/models/trained/t5_clinical_model"
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    print(f"🔧 Device: {device}")
    print(f"📁 Model: {model_path}")
    
    try:
        # Load model and tokenizer
        print("📥 Loading model...")
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = T5ForConditionalGeneration.from_pretrained(model_path)
        model.to(device)
        model.eval()
        print("✅ Model loaded successfully")
        
        # Model info
        total_params = sum(p.numel() for p in model.parameters())
        print(f"📊 Parameters: {total_params:,} (~{total_params * 4 / 1024 / 1024:.1f} MB)")
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return
    
    # Test queries
    test_queries = [
        "How many patients do we have?",
        "List all male patients", 
        "Find patients with diabetes",
        "Show high-cost patients",
        "List all medications"
    ]
    
    print("\n🧪 Testing Queries:")
    print("-" * 30)
    
    results = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"{i}. {query}")
        
        # Add schema context
        schema_context = """Database Schema: clinical_data
Tables: patients, organizations, providers, encounters, conditions, medications, procedures, observations, allergies, careplans, immunizations, claims, payers
Key relationships: 
- patients.id -> encounters.patient_id
- providers.id -> encounters.provider_id  
- organizations.id -> providers.organization_id
- encounters.id -> conditions.encounter_id
- encounters.id -> medications.encounter_id
- encounters.id -> procedures.encounter_id
- encounters.id -> observations.encounter_id
- payers.id -> claims.payer_id"""
        
        input_text = f"translate to sql: {query} {schema_context}"
        
        # Generate SQL
        start_time = time.time()
        
        inputs = tokenizer(
            input_text,
            return_tensors="pt",
            max_length=512,
            truncation=True,
            padding=True
        ).to(device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=256,
                num_beams=2,  # Reduced for speed
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
        
        generated_sql = tokenizer.decode(outputs[0], skip_special_tokens=True)
        generation_time = time.time() - start_time
        
        # Analyze result
        sql_upper = generated_sql.upper()
        analysis = {
            'has_select': sql_upper.startswith('SELECT'),
            'has_from': 'FROM' in sql_upper,
            'has_clinical_schema': 'clinical_data.' in generated_sql,
            'has_where': 'WHERE' in sql_upper,
            'has_join': 'JOIN' in sql_upper,
            'length': len(generated_sql),
            'time': generation_time
        }
        
        results.append({
            'query': query,
            'sql': generated_sql,
            'analysis': analysis
        })
        
        print(f"   SQL: {generated_sql}")
        print(f"   Time: {generation_time:.2f}s")
        print(f"   Schema: {'✅' if analysis['has_clinical_schema'] else '❌'}")
        print(f"   Valid: {'✅' if analysis['has_select'] and analysis['has_from'] else '❌'}")
        print()
    
    # Summary
    print("📊 SUMMARY:")
    print("-" * 30)
    
    total_queries = len(results)
    schema_compliant = sum(1 for r in results if r['analysis']['has_clinical_schema'])
    valid_sql = sum(1 for r in results if r['analysis']['has_select'] and r['analysis']['has_from'])
    avg_time = sum(r['analysis']['time'] for r in results) / total_queries
    
    print(f"Total Queries: {total_queries}")
    print(f"Schema Compliant: {schema_compliant}/{total_queries} ({schema_compliant/total_queries*100:.1f}%)")
    print(f"Valid SQL: {valid_sql}/{total_queries} ({valid_sql/total_queries*100:.1f}%)")
    print(f"Average Time: {avg_time:.2f}s")
    
    # Performance assessment
    print(f"\n🎯 ASSESSMENT:")
    if schema_compliant == total_queries and valid_sql == total_queries:
        print("✅ EXCELLENT - Model performs very well!")
    elif schema_compliant >= total_queries * 0.8 and valid_sql >= total_queries * 0.8:
        print("✅ GOOD - Model performs well with minor issues")
    elif schema_compliant >= total_queries * 0.6 and valid_sql >= total_queries * 0.6:
        print("⚠️ MODERATE - Model needs improvement")
    else:
        print("❌ POOR - Model needs significant work")
    
    # Test one example from the actual test set
    print(f"\n🔍 TESTING REAL EXAMPLE:")
    print("-" * 30)
    
    try:
        with open('data/processed/final_merged_dataset/test_data.json', 'r') as f:
            test_data = json.load(f)
        
        # Get first example
        example = test_data[0]
        nlq = example['input_text'].split('Database Schema:')[0].replace('translate to sql: ', '').strip()
        expected_sql = example['target_text']
        
        print(f"Question: {nlq}")
        print(f"Expected: {expected_sql}")
        
        # Generate
        input_text = example['input_text']
        inputs = tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True).to(device)
        
        with torch.no_grad():
            outputs = model.generate(**inputs, max_length=256, num_beams=2)
        
        generated_sql = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"Generated: {generated_sql}")
        
        # Compare
        if generated_sql.strip() == expected_sql.strip():
            print("✅ EXACT MATCH!")
        elif 'clinical_data.' in generated_sql and 'SELECT' in generated_sql.upper():
            print("✅ GOOD - Valid SQL with correct schema")
        else:
            print("❌ NEEDS IMPROVEMENT")
            
    except Exception as e:
        print(f"❌ Could not test real example: {e}")
    
    print(f"\n✅ Quick test complete!")
    
    # Save results
    report = {
        'timestamp': datetime.now().isoformat(),
        'model_path': model_path,
        'device': str(device),
        'total_parameters': total_params,
        'test_results': results,
        'summary': {
            'total_queries': total_queries,
            'schema_compliant': schema_compliant,
            'valid_sql': valid_sql,
            'avg_time': avg_time,
            'schema_compliance_rate': schema_compliant/total_queries,
            'valid_sql_rate': valid_sql/total_queries
        }
    }
    
    with open('QUICK_MODEL_TEST_RESULTS.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"📄 Results saved to: QUICK_MODEL_TEST_RESULTS.json")

if __name__ == "__main__":
    quick_test_model()