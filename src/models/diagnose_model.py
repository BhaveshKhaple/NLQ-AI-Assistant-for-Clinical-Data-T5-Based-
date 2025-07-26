#!/usr/bin/env python3
"""
Model Diagnostic Script
Simple script to test individual queries and diagnose model issues.
"""

import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer

def test_individual_queries():
    """Test individual queries to diagnose model issues."""
    
    model_path = "d:/projects/healthca/models/trained/t5_clinical_model/final_model"
    
    print("🔍 Loading model for diagnosis...")
    tokenizer = T5Tokenizer.from_pretrained(model_path)
    model = T5ForConditionalGeneration.from_pretrained(model_path)
    model.eval()
    
    test_queries = [
        "How many patients do we have?",
        "Show me all patients",
        "List all organizations",
        "Find patients with diabetes",
        "What are the most common conditions?"
    ]
    
    print("\n🧪 Testing individual queries:")
    print("=" * 80)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Question: {query}")
        
        # Test different generation parameters
        input_text = f"translate to sql: {query}"
        inputs = tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)
        
        print(f"   Input tokens: {tokenizer.decode(inputs['input_ids'][0])}")
        
        # Try different generation settings
        generation_configs = [
            {"max_length": 128, "num_beams": 1, "do_sample": False, "name": "Greedy"},
            {"max_length": 128, "num_beams": 4, "do_sample": False, "name": "Beam Search"},
            {"max_length": 128, "num_beams": 1, "do_sample": True, "temperature": 0.7, "name": "Sampling"},
        ]
        
        for config in generation_configs:
            name = config.pop("name")
            
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    pad_token_id=tokenizer.pad_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                    **config
                )
            
            generated_sql = tokenizer.decode(outputs[0], skip_special_tokens=True)
            print(f"   {name:12}: {generated_sql}")
        
        print("-" * 80)

def check_training_data_format():
    """Check if the training data format matches what the model expects."""
    
    print("\n🔍 Checking training data format...")
    
    # Load a few examples from training data
    import json
    with open("d:/projects/healthca/data/processed/train_data.json", 'r') as f:
        train_data = json.load(f)
    
    print(f"📊 Training data format check:")
    print(f"   Total examples: {len(train_data)}")
    
    # Show first few examples
    for i, example in enumerate(train_data[:3]):
        print(f"\n   Example {i+1}:")
        print(f"     Input: {example['input_text'][:100]}...")
        print(f"     Target: {example['target_text'][:100]}...")
        print(f"     Category: {example['category']}")

def check_model_config():
    """Check model configuration."""
    
    print("\n🔍 Checking model configuration...")
    
    model_path = "d:/projects/healthca/models/trained/t5_clinical_model/final_model"
    
    # Load config
    from transformers import T5Config
    config = T5Config.from_pretrained(model_path)
    
    print(f"📊 Model Configuration:")
    print(f"   Model type: {config.model_type}")
    print(f"   Vocab size: {config.vocab_size}")
    print(f"   Max length: {config.n_positions if hasattr(config, 'n_positions') else 'Not specified'}")
    print(f"   Hidden size: {config.d_model}")
    print(f"   Num layers: {config.num_layers}")
    print(f"   Num heads: {config.num_heads}")

def main():
    """Main diagnostic function."""
    print("🚀 T5 Clinical Model Diagnostics")
    print("=" * 50)
    
    try:
        # Test individual queries
        test_individual_queries()
        
        # Check training data format
        check_training_data_format()
        
        # Check model config
        check_model_config()
        
        print("\n✅ Diagnostics complete!")
        
    except Exception as e:
        print(f"❌ Error during diagnostics: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()