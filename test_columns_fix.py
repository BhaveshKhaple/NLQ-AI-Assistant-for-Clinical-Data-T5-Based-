#!/usr/bin/env python3
"""
Test the modetest1 model to verify it's working properly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import time
import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer
from nlq.inference_engine import ClinicalInferenceEngine

def test_model_loading():
    """Test if the modetest1 model can be loaded successfully"""
    print("🔧 TESTING MODEL LOADING")
    print("="*50)
    
    model_path = "d:/projects/healthca/models/trained/modetest1"
    
    try:
        print(f"Loading model from: {model_path}")
        
        # Test tokenizer loading
        print("Loading tokenizer...")
        tokenizer = T5Tokenizer.from_pretrained(model_path)
        print(f"✅ Tokenizer loaded successfully")
        print(f"   Vocab size: {tokenizer.vocab_size}")
        print(f"   Model max length: {tokenizer.model_max_length}")
        
        # Test model loading
        print("Loading model...")
        model = T5ForConditionalGeneration.from_pretrained(model_path)
        print(f"✅ Model loaded successfully")
        
        # Get model info
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        model_size_mb = total_params * 4 / 1024 / 1024
        
        print(f"   Total parameters: {total_params:,}")
        print(f"   Trainable parameters: {trainable_params:,}")
        print(f"   Model size: ~{model_size_mb:.1f} MB")
        
        return tokenizer, model
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return None, None

def test_model_inference(tokenizer, model):
    """Test basic inference with the model"""
    print(f"\n🧪 TESTING MODEL INFERENCE")
    print("="*50)
    
    if tokenizer is None or model is None:
        print("❌ Cannot test inference - model not loaded")
        return
    
    # Test queries
    test_queries = [
        "How many patients are in the database?",
        "How many patients received more than 2 immunizations?",
        "Show me all patients with diabetes",
        "Count patients by gender",
        "List all medications"
    ]
    
    model.eval()
    device = torch.device("cpu")
    model.to(device)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test {i}: '{query}' ---")
        
        try:
            # Prepare input
            input_text = f"translate English to SQL: {query}"
            inputs = tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)
            
            # Generate
            start_time = time.time()
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_length=256,
                    num_beams=4,
                    early_stopping=True,
                    do_sample=False
                )
            generation_time = time.time() - start_time
            
            # Decode
            generated_sql = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            print(f"Generated SQL: '{generated_sql}'")
            print(f"Generation time: {generation_time:.3f}s")
            
            # Basic validation
            if generated_sql.strip().upper().startswith('SELECT'):
                print("✅ Valid SQL format")
            else:
                print("❌ Invalid SQL format")
                
        except Exception as e:
            print(f"❌ Error during inference: {e}")

def compare_with_current_model():
    """Compare modetest1 with the current t5_clinical_model"""
    print(f"\n🔄 COMPARING WITH CURRENT MODEL")
    print("="*50)
    
    # Test with current model
    print("Testing current model (t5_clinical_model):")
    try:
        engine = ClinicalInferenceEngine()
        engine.load_model()
        
        query = "How many patients received more than 2 immunizations?"
        result = engine.generate_sql(query)
        
        print(f"Current model SQL: '{result.get('generated_sql', 'N/A')}'")
        print(f"Current model method: {result.get('metadata', {}).get('method', 'Unknown')}")
        
    except Exception as e:
        print(f"❌ Error with current model: {e}")
    
    # Test with modetest1 by temporarily changing config
    print(f"\nTesting modetest1 model:")
    try:
        # Create a temporary engine with modetest1
        engine_test = ClinicalInferenceEngine()
        
        # Manually override the model path
        model_path = "d:/projects/healthca/models/trained/modetest1"
        engine_test.model_path = model_path
        
        if engine_test.load_model():
            query = "How many patients received more than 2 immunizations?"
            result = engine_test.generate_sql(query)
            
            print(f"Modetest1 SQL: '{result.get('generated_sql', 'N/A')}'")
            print(f"Modetest1 method: {result.get('metadata', {}).get('method', 'Unknown')}")
        else:
            print("❌ Failed to load modetest1 model")
            
    except Exception as e:
        print(f"❌ Error with modetest1 model: {e}")

def test_model_compatibility():
    """Test if the model is compatible with the current system"""
    print(f"\n🔍 TESTING MODEL COMPATIBILITY")
    print("="*50)
    
    model_path = "d:/projects/healthca/models/trained/modetest1"
    
    # Check required files
    required_files = [
        "config.json",
        "model.safetensors",
        "tokenizer.json",
        "tokenizer_config.json"
    ]
    
    print("Checking required files:")
    for file in required_files:
        file_path = os.path.join(model_path, file)
        if os.path.exists(file_path):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING")
    
    # Check if it's the same architecture as current model
    try:
        import json
        
        # Load modetest1 config
        with open(os.path.join(model_path, "config.json"), 'r') as f:
            modetest1_config = json.load(f)
        
        # Load current model config
        current_model_path = "d:/projects/healthca/models/trained/t5_clinical_model"
        with open(os.path.join(current_model_path, "config.json"), 'r') as f:
            current_config = json.load(f)
        
        print(f"\nArchitecture comparison:")
        print(f"Modetest1 architecture: {modetest1_config.get('architectures', ['Unknown'])}")
        print(f"Current architecture: {current_config.get('architectures', ['Unknown'])}")
        
        print(f"Modetest1 vocab size: {modetest1_config.get('vocab_size', 'Unknown')}")
        print(f"Current vocab size: {current_config.get('vocab_size', 'Unknown')}")
        
        if modetest1_config.get('architectures') == current_config.get('architectures'):
            print("✅ Same architecture")
        else:
            print("❌ Different architecture")
            
    except Exception as e:
        print(f"❌ Error comparing configs: {e}")

def main():
    """Run all tests"""
    print("🚀 TESTING MODETEST1 MODEL")
    print("="*60)
    
    # Test 1: Model loading
    tokenizer, model = test_model_loading()
    
    # Test 2: Basic inference
    test_model_inference(tokenizer, model)
    
    # Test 3: Compatibility check
    test_model_compatibility()
    
    # Test 4: Comparison with current model
    compare_with_current_model()
    
    print(f"\n" + "="*60)
    print("🏁 TESTING COMPLETE")

if __name__ == "__main__":
    main()