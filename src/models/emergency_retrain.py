#!/usr/bin/env python3
"""
Emergency T5 Model Retraining Script
Implements critical fixes for the failed model with conservative hyperparameters.
"""

import json
import torch
from transformers import (
    T5ForConditionalGeneration, 
    T5Tokenizer, 
    TrainingArguments, 
    Trainer,
    EarlyStoppingCallback
)
from datasets import Dataset
import numpy as np
from typing import Dict, List
import os

class EmergencyT5Retrainer:
    def __init__(self, base_model: str = "t5-small"):
        """Initialize the emergency retrainer."""
        self.base_model = base_model
        self.tokenizer = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        print(f"🚨 Emergency T5 Retraining Setup")
        print(f"   Base model: {base_model}")
        print(f"   Device: {self.device}")
    
    def load_and_prepare_data(self) -> tuple:
        """Load and prepare training data with consistent format."""
        print("📊 Loading and preparing training data...")
        
        # Load the new 10K training data
        try:
            with open("d:/projects/healthca/data/processed/final_10k_dataset/train_data.json", 'r') as f:
                data = json.load(f)
            print(f"   Using new 10K dataset")
        except FileNotFoundError:
            # Fallback to original data if 10K dataset not found
            with open("d:/projects/healthca/data/processed/clinical_nlq_training_data.json", 'r') as f:
                dataset = json.load(f)
            data = dataset['data']
            print(f"   Using original dataset (fallback)")
        print(f"   Loaded {len(data)} examples")
        
        # Check if data is already in the correct format (new 10K dataset)
        if isinstance(data, list) and len(data) > 0 and 'input_text' in data[0]:
            # New 10K dataset format - already properly formatted
            formatted_data = data
            print(f"   Data already in correct format")
        else:
            # Old format - needs conversion
            formatted_data = []
            for item in data:
                formatted_item = {
                    "input_text": f"translate to sql: {item['nlq']}",  # Simple format
                    "target_text": item['sql'],
                    "category": item.get('category', 'general')
                }
                formatted_data.append(formatted_item)
            print(f"   Converted old format to new format")
        
        # Create curriculum learning stages based on query complexity
        # Analyze queries to categorize them
        basic_data = []
        intermediate_data = []
        advanced_data = []
        
        for item in formatted_data:
            sql_upper = item['target_text'].upper()
            input_lower = item['input_text'].lower()
            
            # Basic queries: simple SELECT, COUNT without JOINs
            if ('COUNT(*)' in sql_upper and 'JOIN' not in sql_upper) or \
               ('SELECT' in sql_upper and 'JOIN' not in sql_upper and 'GROUP BY' not in sql_upper):
                basic_data.append(item)
            # Advanced queries: multiple JOINs, complex conditions
            elif sql_upper.count('JOIN') > 1 or 'HAVING' in sql_upper or \
                 ('both' in input_lower and 'and' in input_lower):
                advanced_data.append(item)
            # Intermediate: single JOINs, GROUP BY, aggregations
            else:
                intermediate_data.append(item)
        
        all_data = formatted_data
        
        print(f"   Basic queries: {len(basic_data)}")
        print(f"   Intermediate queries: {len(intermediate_data)}")
        print(f"   Advanced queries: {len(advanced_data)}")
        print(f"   Total queries: {len(all_data)}")
        
        return basic_data, intermediate_data, advanced_data
    
    def create_datasets(self, data: List[Dict]) -> tuple:
        """Create train/validation datasets."""
        # Split data
        train_size = int(0.8 * len(data))
        train_data = data[:train_size]
        val_data = data[train_size:]
        
        print(f"   Train: {len(train_data)}, Validation: {len(val_data)}")
        
        # Create HuggingFace datasets
        train_dataset = Dataset.from_list(train_data)
        val_dataset = Dataset.from_list(val_data)
        
        return train_dataset, val_dataset
    
    def tokenize_data(self, dataset: Dataset) -> Dataset:
        """Tokenize the dataset."""
        def tokenize_function(examples):
            # Tokenize inputs
            inputs = self.tokenizer(
                examples['input_text'],
                max_length=256,  # Reduced for stability
                truncation=True,
                padding=True,
                return_tensors="pt"
            )
            
            # Tokenize targets
            targets = self.tokenizer(
                examples['target_text'],
                max_length=512,
                truncation=True,
                padding=True,
                return_tensors="pt"
            )
            
            inputs['labels'] = targets['input_ids']
            return inputs
        
        return dataset.map(tokenize_function, batched=True)
    
    def compute_metrics(self, eval_pred):
        """Compute SQL validity metrics during training."""
        predictions, labels = eval_pred
        
        # Decode predictions and labels
        decoded_preds = self.tokenizer.batch_decode(predictions, skip_special_tokens=True)
        decoded_labels = self.tokenizer.batch_decode(labels, skip_special_tokens=True)
        
        # Count valid SQL queries
        valid_sql_count = 0
        has_select_count = 0
        has_from_count = 0
        has_schema_count = 0
        
        for pred in decoded_preds:
            pred_upper = pred.upper()
            
            if pred_upper.startswith('SELECT'):
                has_select_count += 1
            
            if 'FROM' in pred_upper:
                has_from_count += 1
                
            if 'clinical_data.' in pred:
                has_schema_count += 1
            
            # Valid SQL: has SELECT, FROM, and schema
            if (pred_upper.startswith('SELECT') and 
                'FROM' in pred_upper and 
                'clinical_data.' in pred):
                valid_sql_count += 1
        
        total = len(decoded_preds)
        
        return {
            "sql_validity_rate": valid_sql_count / total,
            "select_rate": has_select_count / total,
            "from_rate": has_from_count / total,
            "schema_rate": has_schema_count / total
        }
    
    def create_conservative_training_args(self, output_dir: str, stage_name: str) -> TrainingArguments:
        """Create conservative training arguments for stable training."""
        return TrainingArguments(
            output_dir=output_dir,
            
            # Conservative learning settings
            learning_rate=5e-5,              # Very conservative
            num_train_epochs=8,              # More epochs for convergence
            per_device_train_batch_size=2,   # Small batches for stability
            gradient_accumulation_steps=8,   # Effective batch size = 16
            
            # Stability improvements
            warmup_steps=200,                # Gradual warmup
            weight_decay=0.01,               # Prevent overfitting
            max_grad_norm=1.0,               # Gradient clipping
            
            # Monitoring and checkpointing
            save_steps=50,                   # Frequent saves
            eval_steps=50,                   # Frequent evaluation
            logging_steps=10,                # Detailed logging
            
            # Quality control
            eval_strategy="steps",
            save_strategy="steps",
            load_best_model_at_end=True,
            metric_for_best_model="sql_validity_rate",
            greater_is_better=True,
            save_total_limit=3,
            
            # Performance
            fp16=False,                      # Disable for stability
            dataloader_num_workers=0,        # Stability on Windows
            seed=42,                         # Reproducibility
            
            # Reporting
            report_to=None,                  # Disable wandb
            run_name=f"emergency_retrain_{stage_name}"
        )
    
    def train_stage(self, train_dataset: Dataset, val_dataset: Dataset, 
                   stage_name: str, learning_rate: float = 5e-5) -> str:
        """Train a single stage with curriculum learning."""
        print(f"\n🎯 Training Stage: {stage_name}")
        print(f"   Learning rate: {learning_rate}")
        print(f"   Train examples: {len(train_dataset)}")
        print(f"   Val examples: {len(val_dataset)}")
        
        # Initialize model and tokenizer
        if self.model is None:
            print(f"   Loading base model: {self.base_model}")
            self.tokenizer = T5Tokenizer.from_pretrained(self.base_model)
            self.model = T5ForConditionalGeneration.from_pretrained(self.base_model)
        
        # Tokenize datasets
        print("   Tokenizing datasets...")
        train_tokenized = self.tokenize_data(train_dataset)
        val_tokenized = self.tokenize_data(val_dataset)
        
        # Setup training arguments
        output_dir = f"d:/projects/healthca/models/emergency_retrain/{stage_name}"
        os.makedirs(output_dir, exist_ok=True)
        
        training_args = self.create_conservative_training_args(output_dir, stage_name)
        training_args.learning_rate = learning_rate  # Override learning rate
        
        # Create trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_tokenized,
            eval_dataset=val_tokenized,
            compute_metrics=self.compute_metrics,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=5)]
        )
        
        # Train
        print("   Starting training...")
        trainer.train()
        
        # Save best model
        best_model_path = f"{output_dir}/best_model"
        trainer.save_model(best_model_path)
        self.tokenizer.save_pretrained(best_model_path)
        
        print(f"   ✅ Stage completed. Model saved to: {best_model_path}")
        
        # Load best model for next stage
        self.model = T5ForConditionalGeneration.from_pretrained(best_model_path)
        
        return best_model_path
    
    def emergency_retrain(self) -> str:
        """Execute emergency retraining with curriculum learning."""
        print("🚨 Starting Emergency Retraining Process")
        print("=" * 60)
        
        # Load and prepare data
        basic_data, intermediate_data, advanced_data = self.load_and_prepare_data()
        
        # Stage 1: Basic queries only
        print("\n📚 STAGE 1: Basic Queries (Foundation)")
        basic_train, basic_val = self.create_datasets(basic_data)
        stage1_path = self.train_stage(basic_train, basic_val, "stage1_basic", learning_rate=1e-4)
        
        # Stage 2: Basic + Intermediate
        print("\n📚 STAGE 2: Basic + Intermediate Queries")
        combined_data = basic_data + intermediate_data
        combined_train, combined_val = self.create_datasets(combined_data)
        stage2_path = self.train_stage(combined_train, combined_val, "stage2_intermediate", learning_rate=5e-5)
        
        # Stage 3: All queries (including advanced)
        print("\n📚 STAGE 3: All Queries (Final)")
        all_data = basic_data + intermediate_data + advanced_data
        all_train, all_val = self.create_datasets(all_data)
        final_path = self.train_stage(all_train, all_val, "stage3_final", learning_rate=3e-5)
        
        print("\n🎉 Emergency Retraining Complete!")
        print(f"   Final model saved to: {final_path}")
        
        return final_path
    
    def quick_test(self, model_path: str):
        """Quick test of the retrained model."""
        print(f"\n🧪 Quick Testing: {model_path}")
        
        # Load model
        tokenizer = T5Tokenizer.from_pretrained(model_path)
        model = T5ForConditionalGeneration.from_pretrained(model_path)
        model.eval()
        
        test_queries = [
            "How many patients do we have?",
            "Show me all patients",
            "Find patients with diabetes"
        ]
        
        for query in test_queries:
            input_text = f"translate to sql: {query}"
            inputs = tokenizer(input_text, return_tensors="pt", max_length=256, truncation=True)
            
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_length=256,
                    num_beams=4,
                    early_stopping=True,
                    pad_token_id=tokenizer.pad_token_id
                )
            
            generated_sql = tokenizer.decode(outputs[0], skip_special_tokens=True)
            print(f"   Q: {query}")
            print(f"   A: {generated_sql}")
            print()

def main():
    """Main emergency retraining function."""
    print("🚨 T5 Clinical Model Emergency Retraining")
    print("This will completely retrain the model with conservative hyperparameters.")
    
    # Initialize retrainer
    retrainer = EmergencyT5Retrainer(base_model="t5-small")
    
    try:
        # Execute emergency retraining
        final_model_path = retrainer.emergency_retrain()
        
        # Quick test
        retrainer.quick_test(final_model_path)
        
        print("\n✅ Emergency retraining completed successfully!")
        print(f"📁 New model location: {final_model_path}")
        print("\n🎯 Next steps:")
        print("   1. Test the new model with the quick_model_test.py script")
        print("   2. If performance is acceptable (>60% accuracy), deploy")
        print("   3. If still poor, consider T5-base model or dataset expansion")
        
    except Exception as e:
        print(f"\n❌ Emergency retraining failed: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n🔧 Troubleshooting suggestions:")
        print("   1. Check available memory (model needs ~2GB RAM)")
        print("   2. Ensure training data is accessible")
        print("   3. Try with smaller batch size (per_device_train_batch_size=1)")
        print("   4. Consider using T5-base if T5-small continues to fail")

if __name__ == "__main__":
    main()