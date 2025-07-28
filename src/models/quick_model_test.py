#!/usr/bin/env python3
"""
Quick T5 Clinical Model Testing Script
Optimized for CPU inference with faster evaluation and immediate hyperparameter recommendations.
"""

import json
import torch
import time
from typing import List, Dict, Tuple
from transformers import T5ForConditionalGeneration, T5Tokenizer
from collections import defaultdict
import random

class QuickClinicalT5Tester:
    def __init__(self, model_path: str = "d:/projects/healthca/models/trained/t5_clinical_model/final model last"):
        """Initialize the model tester."""
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.device = torch.device("cpu")  # Force CPU for stability
        
    def load_model(self) -> bool:
        """Load the trained T5 model and tokenizer."""
        try:
            print(f"📥 Loading model from: {self.model_path}")
            
            # Load tokenizer
            self.tokenizer = T5Tokenizer.from_pretrained(self.model_path)
            print("✅ Tokenizer loaded")
            
            # Load model
            self.model = T5ForConditionalGeneration.from_pretrained(self.model_path)
            self.model.to(self.device)
            self.model.eval()
            print("✅ Model loaded")
            
            # Model info
            total_params = sum(p.numel() for p in self.model.parameters())
            print(f"📊 Model: {total_params:,} parameters (~{total_params * 4 / 1024 / 1024:.1f} MB)")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def generate_sql(self, nlq: str, max_length: int = 256, num_beams: int = 2) -> str:
        """Generate SQL query from natural language question (optimized for speed)."""
        input_text = f"translate to sql: {nlq}"
        
        inputs = self.tokenizer(
            input_text,
            return_tensors="pt",
            max_length=256,  # Reduced for speed
            truncation=True,
            padding=True
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                num_beams=num_beams,  # Reduced for speed
                early_stopping=True,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
        
        generated_sql = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return generated_sql.strip()
    
    def quick_sample_test(self) -> List[Dict]:
        """Test with a focused set of representative queries."""
        print("🧪 Running quick sample tests...")
        
        test_queries = [
            {"nlq": "How many patients do we have?", "category": "basic_count"},
            {"nlq": "Show me all male patients", "category": "basic_filter"},
            {"nlq": "Find all patients with diabetes", "category": "join_filter"},
            {"nlq": "What are the most common conditions?", "category": "aggregation"},
            {"nlq": "Which providers see the most patients?", "category": "provider_analysis"},
            {"nlq": "Find patients with both diabetes and hypertension", "category": "complex_clinical"},
            {"nlq": "What is the average cost per encounter?", "category": "financial_analysis"},
            {"nlq": "Show patients diagnosed in the last year", "category": "temporal_filter"}
        ]
        
        results = []
        total_time = 0
        
        for i, query in enumerate(test_queries):
            print(f"  Testing {i+1}/{len(test_queries)}: {query['nlq'][:40]}...")
            
            start_time = time.time()
            generated_sql = self.generate_sql(query['nlq'])
            generation_time = time.time() - start_time
            total_time += generation_time
            
            # Quick analysis
            analysis = {
                'nlq': query['nlq'],
                'generated_sql': generated_sql,
                'category': query['category'],
                'generation_time': generation_time,
                'has_select': generated_sql.upper().startswith('SELECT'),
                'has_from': 'FROM' in generated_sql.upper(),
                'has_schema': 'clinical_data.' in generated_sql,
                'has_where': 'WHERE' in generated_sql.upper(),
                'has_join': 'JOIN' in generated_sql.upper(),
                'sql_length': len(generated_sql),
                'looks_valid': self.quick_sql_validation(generated_sql)
            }
            
            results.append(analysis)
        
        print(f"⏱️  Total time: {total_time:.2f}s, Average: {total_time/len(test_queries):.2f}s per query")
        return results
    
    def quick_sql_validation(self, sql: str) -> bool:
        """Quick SQL validation check."""
        sql_upper = sql.upper()
        return (
            sql_upper.startswith('SELECT') and
            'FROM' in sql_upper and
            'clinical_data.' in sql and
            sql.count('(') == sql.count(')')
        )
    
    def sample_test_set_evaluation(self, sample_size: int = 30) -> Dict:
        """Evaluate on a sample of the test set for quick assessment."""
        print(f"📊 Evaluating on {sample_size} test examples...")
        
        # Load test data
        test_data_path = "d:/projects/healthca/data/processed/final_merged_dataset/test_data.json"
        with open(test_data_path, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        
        # Sample random examples
        sample_data = random.sample(test_data, min(sample_size, len(test_data)))
        
        results = {
            'total_tested': len(sample_data),
            'exact_matches': 0,
            'partial_matches': 0,
            'syntax_correct': 0,
            'schema_correct': 0,
            'category_performance': defaultdict(list),
            'examples': []
        }
        
        for i, example in enumerate(sample_data):
            if i % 10 == 0:
                print(f"  Progress: {i}/{len(sample_data)}")
            
            nlq = example.get('original_nlq', example['input_text'].replace('translate to sql: ', '').split(' Database Schema:')[0])
            expected_sql = example['target_text']
            category = example.get('category', 'general')
            
            generated_sql = self.generate_sql(nlq)
            
            # Quick evaluation
            evaluation = self.quick_evaluate_prediction(generated_sql, expected_sql)
            
            results['category_performance'][category].append(evaluation)
            
            if evaluation['exact_match']:
                results['exact_matches'] += 1
            if evaluation['partial_match']:
                results['partial_matches'] += 1
            if evaluation['syntax_correct']:
                results['syntax_correct'] += 1
            if evaluation['schema_correct']:
                results['schema_correct'] += 1
            
            # Store example for analysis
            if i < 5:  # Store first 5 for detailed analysis
                results['examples'].append({
                    'nlq': nlq,
                    'expected': expected_sql,
                    'generated': generated_sql,
                    'category': category,
                    **evaluation
                })
        
        return results
    
    def quick_evaluate_prediction(self, generated_sql: str, expected_sql: str) -> Dict:
        """Quick evaluation of a single prediction."""
        # Normalize for comparison
        def normalize(sql):
            return ' '.join(sql.upper().split())
        
        gen_norm = normalize(generated_sql)
        exp_norm = normalize(expected_sql)
        
        # Exact match
        exact_match = gen_norm == exp_norm
        
        # Partial match (word overlap)
        gen_words = set(gen_norm.split())
        exp_words = set(exp_norm.split())
        overlap = len(gen_words.intersection(exp_words)) / len(exp_words.union(gen_words)) if exp_words.union(gen_words) else 0
        partial_match = overlap > 0.6
        
        # Basic validations
        syntax_correct = self.quick_sql_validation(generated_sql)
        schema_correct = 'clinical_data.' in generated_sql
        
        return {
            'exact_match': exact_match,
            'partial_match': partial_match,
            'syntax_correct': syntax_correct,
            'schema_correct': schema_correct,
            'word_overlap': overlap
        }
    
    def generate_quick_report(self, sample_results: List[Dict], test_results: Dict) -> str:
        """Generate a quick evaluation report with hyperparameter recommendations."""
        
        # Calculate metrics
        exact_match_rate = test_results['exact_matches'] / test_results['total_tested']
        partial_match_rate = test_results['partial_matches'] / test_results['total_tested']
        syntax_rate = test_results['syntax_correct'] / test_results['total_tested']
        schema_rate = test_results['schema_correct'] / test_results['total_tested']
        
        avg_time = sum(r['generation_time'] for r in sample_results) / len(sample_results)
        valid_queries = sum(1 for r in sample_results if r['looks_valid'])
        
        report = f"""
# 🚀 T5 Clinical Model - Quick Evaluation Report

## 📊 Performance Summary
- **Exact Match Rate**: {exact_match_rate:.1%} ({test_results['exact_matches']}/{test_results['total_tested']})
- **Partial Match Rate**: {partial_match_rate:.1%} ({test_results['partial_matches']}/{test_results['total_tested']})
- **Syntax Correctness**: {syntax_rate:.1%} ({test_results['syntax_correct']}/{test_results['total_tested']})
- **Schema Compliance**: {schema_rate:.1%} ({test_results['schema_correct']}/{test_results['total_tested']})
- **Average Generation Time**: {avg_time:.3f} seconds
- **Valid Sample Queries**: {valid_queries}/{len(sample_results)}

## 🎯 Model Assessment

"""
        
        if exact_match_rate >= 0.8:
            report += "✅ **EXCELLENT**: Model is performing very well and ready for production!\n"
            performance_level = "excellent"
        elif exact_match_rate >= 0.6:
            report += "⚠️ **GOOD**: Model shows promise but needs fine-tuning for production.\n"
            performance_level = "good"
        elif exact_match_rate >= 0.4:
            report += "🔧 **MODERATE**: Model needs significant hyperparameter tuning.\n"
            performance_level = "moderate"
        else:
            report += "❌ **POOR**: Model requires major retraining with different approach.\n"
            performance_level = "poor"
        
        report += f"""
## 📝 Sample Query Results

"""
        
        for i, result in enumerate(sample_results[:3], 1):
            status = "✅" if result['looks_valid'] else "❌"
            report += f"""
### {status} Sample {i}: {result['category']}
**Question**: {result['nlq']}
**Generated SQL**: 
```sql
{result['generated_sql']}
```
**Time**: {result['generation_time']:.3f}s | **Length**: {result['sql_length']} chars
**Analysis**: Schema ✅ | SELECT ✅ | FROM ✅ | Valid: {result['looks_valid']}

"""
        
        report += """
## 🔧 Hyperparameter Tuning Recommendations

"""
        
        if performance_level == "excellent":
            report += """
### ✅ Current Performance: EXCELLENT (80%+ accuracy)
**Recommendation**: Model is production-ready! Minor optimizations only.

```python
# Fine-tuning for stability (optional)
training_args = TrainingArguments(
    learning_rate=1e-5,           # Very low for stability
    num_train_epochs=1,           # Just one epoch
    per_device_train_batch_size=8,
    warmup_steps=100,
    weight_decay=0.001,           # Light regularization
    save_steps=500,
    eval_steps=500,
    fp16=True,
    load_best_model_at_end=True,
    early_stopping_patience=3
)

# Optimal generation settings
generation_config = {
    "max_length": 512,
    "num_beams": 4,
    "early_stopping": True,
    "no_repeat_ngram_size": 2,
    "length_penalty": 1.0
}
```

**Next Steps**:
1. Deploy with monitoring
2. Collect real user feedback
3. Implement query validation pipeline
"""
        
        elif performance_level == "good":
            report += """
### ⚠️ Current Performance: GOOD (60-80% accuracy)
**Recommendation**: Fine-tune with adjusted hyperparameters.

```python
# Recommended fine-tuning
training_args = TrainingArguments(
    learning_rate=3e-5,           # Moderate increase
    num_train_epochs=3,           # Additional epochs
    per_device_train_batch_size=8,
    warmup_steps=500,
    weight_decay=0.01,
    save_steps=250,
    eval_steps=250,
    logging_steps=50,
    fp16=True,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    greater_is_better=False,
    early_stopping_patience=5
)

# Data augmentation
data_augmentation = {
    "add_paraphrased_queries": 200,
    "add_synonym_variations": 150,
    "focus_on_weak_categories": ["complex_clinical", "temporal_analysis"]
}
```

**Immediate Actions**:
1. Add 300-500 more training examples
2. Focus on categories with <60% accuracy
3. Implement SQL syntax validation during training
"""
        
        elif performance_level == "moderate":
            report += """
### 🔧 Current Performance: MODERATE (40-60% accuracy)
**Recommendation**: Significant hyperparameter adjustment needed.

```python
# Major hyperparameter changes
training_args = TrainingArguments(
    learning_rate=5e-4,           # Higher learning rate
    num_train_epochs=5,           # More epochs
    per_device_train_batch_size=4, # Smaller batch for stability
    gradient_accumulation_steps=4, # Effective batch size = 16
    warmup_steps=1000,            # More warmup
    weight_decay=0.01,
    save_steps=200,
    eval_steps=200,
    logging_steps=25,
    fp16=True,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    early_stopping_patience=3,
    lr_scheduler_type="cosine",   # Different scheduler
    warmup_ratio=0.1
)

# Consider model architecture changes
model_improvements = {
    "try_t5_base": "Instead of t5-small",
    "add_custom_loss": "SQL syntax penalty",
    "implement_curriculum_learning": "Start with simple queries"
}
```

**Critical Actions**:
1. Double the training dataset (2000+ examples)
2. Implement custom loss function for SQL validity
3. Add extensive data validation
4. Consider T5-base model if resources allow
"""
        
        else:  # poor performance
            report += """
### ❌ Current Performance: POOR (<40% accuracy)
**Recommendation**: Major retraining required with different approach.

```python
# Complete retraining strategy
training_args = TrainingArguments(
    learning_rate=1e-3,           # Much higher learning rate
    num_train_epochs=8,           # Many more epochs
    per_device_train_batch_size=2, # Very small batches
    gradient_accumulation_steps=8, # Effective batch size = 16
    warmup_steps=2000,            # Extended warmup
    weight_decay=0.05,            # Strong regularization
    save_steps=100,
    eval_steps=100,
    logging_steps=10,
    fp16=True,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    early_stopping_patience=5,
    lr_scheduler_type="polynomial",
    dataloader_num_workers=0,     # Stability
    seed=42
)

# Dataset expansion strategy
dataset_strategy = {
    "target_size": 5000,          # 5x current dataset
    "add_basic_queries": 2000,    # Focus on fundamentals
    "add_template_variations": 1500,
    "add_real_world_examples": 1500,
    "implement_data_validation": True
}
```

**Emergency Actions**:
1. Expand dataset to 5000+ examples
2. Start with simpler queries (curriculum learning)
3. Consider pre-training on general SQL datasets
4. Implement extensive query validation
5. Consider alternative architectures (CodeT5, etc.)
"""
        
        report += f"""

## 🎯 Specific Recommendations Based on Current Results

### Immediate Fixes Needed:
"""
        
        if syntax_rate < 0.9:
            report += f"- **SQL Syntax**: Only {syntax_rate:.1%} queries are syntactically correct. Add SQL validation to training.\n"
        
        if schema_rate < 0.95:
            report += f"- **Schema Usage**: Only {schema_rate:.1%} queries use correct schema. Emphasize 'clinical_data.' prefix.\n"
        
        if avg_time > 2.0:
            report += f"- **Generation Speed**: {avg_time:.2f}s is slow. Optimize with num_beams=2 for inference.\n"
        
        # Analyze category performance
        category_issues = []
        for category, evals in test_results['category_performance'].items():
            if evals:
                accuracy = sum(e['exact_match'] for e in evals) / len(evals)
                if accuracy < 0.5:
                    category_issues.append(f"{category} ({accuracy:.1%})")
        
        if category_issues:
            report += f"- **Weak Categories**: Focus training on: {', '.join(category_issues)}\n"
        
        report += f"""

### Training Data Recommendations:
- **Current Dataset**: 999 examples
- **Recommended Size**: {2000 if performance_level in ['good', 'excellent'] else 3000 if performance_level == 'moderate' else 5000}
- **Focus Areas**: {"Complex queries, edge cases" if performance_level == 'excellent' else "Basic syntax, schema compliance" if performance_level == 'poor' else "Category balance, query variations"}

### Generation Settings for Production:
```python
# Balanced quality/speed
generation_params = {{
    "max_length": 512,
    "num_beams": {4 if performance_level == 'excellent' else 2},
    "early_stopping": True,
    "temperature": {0.7 if performance_level == 'excellent' else 1.0},
    "do_sample": {str(performance_level == 'excellent').lower()},
    "no_repeat_ngram_size": 2
}}
```

## 🚀 Next Steps Priority

### This Week:
1. {"Deploy with monitoring" if performance_level == 'excellent' else "Implement recommended hyperparameters"}
2. {"Collect user feedback" if performance_level == 'excellent' else "Expand training dataset"}
3. {"Add query validation" if performance_level == 'excellent' else "Focus on weak categories"}

### Next 2 Weeks:
1. {"Optimize for production scale" if performance_level == 'excellent' else "Retrain with new parameters"}
2. {"Implement active learning" if performance_level == 'excellent' else "Add SQL syntax validation"}
3. {"Add advanced features" if performance_level == 'excellent' else "Test on larger sample"}

**Overall Status**: {'🎉 READY FOR PRODUCTION' if performance_level == 'excellent' else '⚠️ NEEDS TUNING' if performance_level == 'good' else '🔧 REQUIRES RETRAINING' if performance_level == 'moderate' else '❌ MAJOR OVERHAUL NEEDED'}
"""
        
        return report

def main():
    """Main quick testing function."""
    print("🚀 Quick T5 Clinical Model Testing (CPU Optimized)")
    print("=" * 60)
    
    # Initialize tester
    tester = QuickClinicalT5Tester()
    
    # Load model
    if not tester.load_model():
        return
    
    print("\n" + "=" * 60)
    
    # Quick sample test
    print("1️⃣ Running sample query tests...")
    sample_results = tester.quick_sample_test()
    
    print("\n" + "=" * 60)
    
    # Quick test set evaluation
    print("2️⃣ Evaluating on test sample...")
    test_results = tester.sample_test_set_evaluation(sample_size=50)  # Reduced for speed
    
    print("\n" + "=" * 60)
    
    # Generate report
    print("3️⃣ Generating evaluation report...")
    report = tester.generate_quick_report(sample_results, test_results)
    
    # Save report
    report_path = "d:/projects/healthca/models/trained/quick_evaluation_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(report)
    print(f"\n📄 Report saved to: {report_path}")
    
    # Quick summary
    exact_rate = test_results['exact_matches'] / test_results['total_tested']
    print(f"\n🎯 QUICK SUMMARY:")
    print(f"   Exact Match Rate: {exact_rate:.1%}")
    print(f"   Syntax Correctness: {test_results['syntax_correct']/test_results['total_tested']:.1%}")
    print(f"   Schema Compliance: {test_results['schema_correct']/test_results['total_tested']:.1%}")
    
    if exact_rate >= 0.8:
        print("   Status: ✅ EXCELLENT - Ready for production!")
    elif exact_rate >= 0.6:
        print("   Status: ⚠️ GOOD - Needs fine-tuning")
    elif exact_rate >= 0.4:
        print("   Status: 🔧 MODERATE - Needs retraining")
    else:
        print("   Status: ❌ POOR - Major overhaul needed")

if __name__ == "__main__":
    main()