#!/usr/bin/env python3
"""
T5 Clinical Model Testing and Evaluation Script
Tests the trained T5 model for NLQ to SQL conversion and provides hyperparameter tuning suggestions.
"""

import json
import torch
import time
import re
from typing import List, Dict, Tuple, Optional
from transformers import T5ForConditionalGeneration, T5Tokenizer
from collections import defaultdict
import pandas as pd
from datetime import datetime

class ClinicalT5ModelTester:
    def __init__(self, model_path: str = "d:/projects/healthca/models/trained/t5_clinical_model/final_model"):
        """Initialize the model tester with the trained model."""
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        print(f"🔧 Using device: {self.device}")
        
    def load_model(self) -> bool:
        """Load the trained T5 model and tokenizer."""
        try:
            print(f"📥 Loading model from: {self.model_path}")
            
            # Load tokenizer
            self.tokenizer = T5Tokenizer.from_pretrained(self.model_path)
            print("✅ Tokenizer loaded successfully")
            
            # Load model
            self.model = T5ForConditionalGeneration.from_pretrained(self.model_path)
            self.model.to(self.device)
            self.model.eval()
            print("✅ Model loaded successfully")
            
            # Print model info
            total_params = sum(p.numel() for p in self.model.parameters())
            trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
            
            print(f"📊 Model Info:")
            print(f"  Total parameters: {total_params:,}")
            print(f"  Trainable parameters: {trainable_params:,}")
            print(f"  Model size: ~{total_params * 4 / 1024 / 1024:.1f} MB")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def generate_sql(self, nlq: str, max_length: int = 512, num_beams: int = 4, 
                    temperature: float = 0.7, do_sample: bool = False) -> str:
        """Generate SQL query from natural language question."""
        if not self.model or not self.tokenizer:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        # Format input
        input_text = f"translate to sql: {nlq}"
        
        # Tokenize
        inputs = self.tokenizer(
            input_text,
            return_tensors="pt",
            max_length=512,
            truncation=True,
            padding=True
        ).to(self.device)
        
        # Generate
        with torch.no_grad():
            if do_sample:
                outputs = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    num_beams=num_beams,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            else:
                outputs = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    num_beams=num_beams,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
        
        # Decode
        generated_sql = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return generated_sql.strip()
    
    def test_sample_queries(self) -> List[Dict]:
        """Test the model with a variety of sample queries."""
        print("🧪 Testing model with sample queries...")
        
        test_queries = [
            # Basic queries
            {
                "nlq": "How many patients do we have?",
                "expected_type": "basic_count",
                "category": "basic"
            },
            {
                "nlq": "Show me all male patients",
                "expected_type": "basic_filter",
                "category": "basic"
            },
            {
                "nlq": "List all healthcare organizations",
                "expected_type": "basic_list",
                "category": "basic"
            },
            
            # Intermediate queries
            {
                "nlq": "Find all patients diagnosed with diabetes",
                "expected_type": "join_filter",
                "category": "intermediate"
            },
            {
                "nlq": "What are the most common medical conditions?",
                "expected_type": "aggregation",
                "category": "intermediate"
            },
            {
                "nlq": "Which patients are taking insulin?",
                "expected_type": "join_filter",
                "category": "intermediate"
            },
            
            # Advanced queries
            {
                "nlq": "Find patients with both diabetes and hypertension",
                "expected_type": "complex_clinical",
                "category": "advanced"
            },
            {
                "nlq": "What is the average healthcare cost per patient?",
                "expected_type": "financial_analysis",
                "category": "advanced"
            },
            {
                "nlq": "Show me elderly patients with chronic conditions on multiple medications",
                "expected_type": "complex_clinical",
                "category": "advanced"
            },
            
            # Complex analytical
            {
                "nlq": "Calculate the trend of diabetes diagnoses over the years",
                "expected_type": "trend_analysis",
                "category": "complex"
            },
            {
                "nlq": "Rank providers by patient volume",
                "expected_type": "provider_ranking",
                "category": "complex"
            },
            
            # Temporal queries
            {
                "nlq": "Find patients diagnosed with COVID in the last 6 months",
                "expected_type": "temporal_filter",
                "category": "temporal"
            }
        ]
        
        results = []
        
        for i, query in enumerate(test_queries):
            print(f"  Testing query {i+1}/{len(test_queries)}: {query['nlq'][:50]}...")
            
            start_time = time.time()
            generated_sql = self.generate_sql(query['nlq'])
            generation_time = time.time() - start_time
            
            result = {
                'nlq': query['nlq'],
                'generated_sql': generated_sql,
                'expected_type': query['expected_type'],
                'category': query['category'],
                'generation_time': generation_time,
                'sql_length': len(generated_sql),
                'has_clinical_data_schema': 'clinical_data.' in generated_sql,
                'has_select': generated_sql.upper().startswith('SELECT'),
                'has_from': 'FROM' in generated_sql.upper(),
                'has_where': 'WHERE' in generated_sql.upper(),
                'has_join': 'JOIN' in generated_sql.upper(),
                'has_group_by': 'GROUP BY' in generated_sql.upper(),
                'has_order_by': 'ORDER BY' in generated_sql.upper()
            }
            
            results.append(result)
        
        return results
    
    def evaluate_on_test_set(self, test_data_path: str = "d:/projects/healthca/data/processed/test_data.json") -> Dict:
        """Evaluate the model on the test dataset."""
        print("📊 Evaluating model on test dataset...")
        
        # Load test data
        with open(test_data_path, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        
        print(f"📋 Loaded {len(test_data)} test examples")
        
        results = {
            'total_examples': len(test_data),
            'correct_predictions': 0,
            'partial_matches': 0,
            'syntax_correct': 0,
            'schema_correct': 0,
            'avg_generation_time': 0,
            'category_performance': defaultdict(list),
            'detailed_results': []
        }
        
        total_time = 0
        
        for i, example in enumerate(test_data):
            if i % 20 == 0:
                print(f"  Progress: {i}/{len(test_data)} ({i/len(test_data)*100:.1f}%)")
            
            # Extract NLQ from input_text
            nlq = example['original_nlq'] if 'original_nlq' in example else example['input_text'].replace('translate to sql: ', '')
            expected_sql = example['target_text']
            category = example['category']
            
            # Generate SQL
            start_time = time.time()
            generated_sql = self.generate_sql(nlq)
            generation_time = time.time() - start_time
            total_time += generation_time
            
            # Evaluate the result
            evaluation = self.evaluate_single_prediction(generated_sql, expected_sql)
            
            detailed_result = {
                'nlq': nlq,
                'expected_sql': expected_sql,
                'generated_sql': generated_sql,
                'category': category,
                'generation_time': generation_time,
                **evaluation
            }
            
            results['detailed_results'].append(detailed_result)
            results['category_performance'][category].append(evaluation)
            
            # Update counters
            if evaluation['exact_match']:
                results['correct_predictions'] += 1
            if evaluation['partial_match']:
                results['partial_matches'] += 1
            if evaluation['syntax_correct']:
                results['syntax_correct'] += 1
            if evaluation['schema_correct']:
                results['schema_correct'] += 1
        
        results['avg_generation_time'] = total_time / len(test_data)
        
        # Calculate category-wise performance
        category_stats = {}
        for category, evals in results['category_performance'].items():
            category_stats[category] = {
                'count': len(evals),
                'exact_match_rate': sum(e['exact_match'] for e in evals) / len(evals),
                'partial_match_rate': sum(e['partial_match'] for e in evals) / len(evals),
                'syntax_correct_rate': sum(e['syntax_correct'] for e in evals) / len(evals),
                'schema_correct_rate': sum(e['schema_correct'] for e in evals) / len(evals)
            }
        
        results['category_stats'] = category_stats
        
        return results
    
    def evaluate_single_prediction(self, generated_sql: str, expected_sql: str) -> Dict:
        """Evaluate a single prediction against the expected SQL."""
        # Normalize SQL for comparison
        def normalize_sql(sql):
            return ' '.join(sql.upper().split())
        
        generated_norm = normalize_sql(generated_sql)
        expected_norm = normalize_sql(expected_sql)
        
        # Exact match
        exact_match = generated_norm == expected_norm
        
        # Partial match (check key components)
        partial_match = False
        if not exact_match:
            # Check if main components are similar
            gen_words = set(generated_norm.split())
            exp_words = set(expected_norm.split())
            overlap = len(gen_words.intersection(exp_words)) / len(exp_words.union(gen_words))
            partial_match = overlap > 0.7  # 70% word overlap
        
        # Syntax correctness (basic check)
        syntax_correct = (
            generated_sql.upper().strip().startswith('SELECT') and
            'FROM' in generated_sql.upper() and
            generated_sql.count('(') == generated_sql.count(')')
        )
        
        # Schema correctness
        schema_correct = 'clinical_data.' in generated_sql
        
        return {
            'exact_match': exact_match,
            'partial_match': partial_match or exact_match,
            'syntax_correct': syntax_correct,
            'schema_correct': schema_correct,
            'word_overlap': len(set(generated_norm.split()).intersection(set(expected_norm.split()))) / max(len(set(expected_norm.split())), 1)
        }
    
    def benchmark_performance(self) -> Dict:
        """Benchmark model performance with different generation parameters."""
        print("⚡ Benchmarking model performance...")
        
        test_queries = [
            "How many patients do we have?",
            "Find all patients with diabetes",
            "What are the most common conditions?",
            "Show me elderly patients on multiple medications",
            "Calculate average healthcare costs by provider"
        ]
        
        parameter_sets = [
            {"num_beams": 1, "temperature": 1.0, "do_sample": False, "name": "Greedy"},
            {"num_beams": 4, "temperature": 1.0, "do_sample": False, "name": "Beam Search (4)"},
            {"num_beams": 8, "temperature": 1.0, "do_sample": False, "name": "Beam Search (8)"},
            {"num_beams": 4, "temperature": 0.7, "do_sample": True, "name": "Sampling (T=0.7)"},
            {"num_beams": 4, "temperature": 0.9, "do_sample": True, "name": "Sampling (T=0.9)"},
        ]
        
        results = {}
        
        for param_set in parameter_sets:
            name = param_set.pop("name")
            print(f"  Testing {name}...")
            
            times = []
            sql_lengths = []
            
            for query in test_queries:
                start_time = time.time()
                generated_sql = self.generate_sql(query, **param_set)
                generation_time = time.time() - start_time
                
                times.append(generation_time)
                sql_lengths.append(len(generated_sql))
            
            results[name] = {
                'avg_time': sum(times) / len(times),
                'avg_sql_length': sum(sql_lengths) / len(sql_lengths),
                'parameters': param_set
            }
        
        return results
    
    def generate_evaluation_report(self, sample_results: List[Dict], 
                                 test_results: Dict, 
                                 benchmark_results: Dict,
                                 output_path: str = None) -> str:
        """Generate a comprehensive evaluation report."""
        
        report = f"""
# T5 Clinical Model Evaluation Report

**Generated on**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Model Path**: {self.model_path}
**Device**: {self.device}

## Executive Summary

### Overall Performance
- **Test Set Accuracy**: {test_results['correct_predictions']}/{test_results['total_examples']} ({test_results['correct_predictions']/test_results['total_examples']*100:.1f}%)
- **Partial Match Rate**: {test_results['partial_matches']}/{test_results['total_examples']} ({test_results['partial_matches']/test_results['total_examples']*100:.1f}%)
- **Syntax Correctness**: {test_results['syntax_correct']}/{test_results['total_examples']} ({test_results['syntax_correct']/test_results['total_examples']*100:.1f}%)
- **Schema Correctness**: {test_results['schema_correct']}/{test_results['total_examples']} ({test_results['schema_correct']/test_results['total_examples']*100:.1f}%)
- **Average Generation Time**: {test_results['avg_generation_time']:.3f} seconds

## Sample Query Results

"""
        
        for i, result in enumerate(sample_results[:5], 1):
            report += f"""
### Sample {i} ({result['category'].title()})
**Question**: {result['nlq']}
**Generated SQL**: 
```sql
{result['generated_sql']}
```
**Generation Time**: {result['generation_time']:.3f}s
**Analysis**: 
- Schema prefix: {'✅' if result['has_clinical_data_schema'] else '❌'}
- Valid SELECT: {'✅' if result['has_select'] else '❌'}
- Has FROM clause: {'✅' if result['has_from'] else '❌'}
- Uses JOINs: {'✅' if result['has_join'] else '❌'}

"""
        
        report += """
## Performance by Category

| Category | Count | Exact Match | Partial Match | Syntax Correct | Schema Correct |
|----------|-------|-------------|---------------|----------------|----------------|
"""
        
        for category, stats in test_results['category_stats'].items():
            report += f"| {category} | {stats['count']} | {stats['exact_match_rate']:.1%} | {stats['partial_match_rate']:.1%} | {stats['syntax_correct_rate']:.1%} | {stats['schema_correct_rate']:.1%} |\n"
        
        report += """
## Generation Parameter Benchmark

| Method | Avg Time (s) | Avg SQL Length | Recommendation |
|--------|--------------|----------------|----------------|
"""
        
        for method, stats in benchmark_results.items():
            recommendation = "⭐ Recommended" if method == "Beam Search (4)" else ""
            report += f"| {method} | {stats['avg_time']:.3f} | {stats['avg_sql_length']:.0f} | {recommendation} |\n"
        
        # Performance Analysis
        exact_match_rate = test_results['correct_predictions'] / test_results['total_examples']
        syntax_rate = test_results['syntax_correct'] / test_results['total_examples']
        
        report += f"""
## Performance Analysis

### Strengths
- **High Syntax Correctness**: {syntax_rate:.1%} of queries are syntactically valid
- **Schema Compliance**: {test_results['schema_correct']/test_results['total_examples']:.1%} use correct schema prefix
- **Fast Generation**: Average {test_results['avg_generation_time']:.3f}s per query

### Areas for Improvement
"""
        
        if exact_match_rate < 0.8:
            report += "- **Exact Match Rate**: Currently at {:.1%}, target should be >80%\n".format(exact_match_rate)
        
        if syntax_rate < 0.95:
            report += "- **SQL Syntax**: {:.1%} syntax correctness, should aim for >95%\n".format(syntax_rate)
        
        # Find worst performing categories
        worst_categories = sorted(test_results['category_stats'].items(), 
                                key=lambda x: x[1]['exact_match_rate'])[:3]
        
        report += "\n### Lowest Performing Categories\n"
        for category, stats in worst_categories:
            report += f"- **{category}**: {stats['exact_match_rate']:.1%} exact match rate ({stats['count']} examples)\n"
        
        report += """
## Hyperparameter Tuning Recommendations

### Current Model Performance Assessment
"""
        
        if exact_match_rate >= 0.8:
            report += "✅ **Model Performance**: GOOD - Ready for production with minor tuning\n"
        elif exact_match_rate >= 0.6:
            report += "⚠️ **Model Performance**: MODERATE - Needs hyperparameter tuning\n"
        else:
            report += "❌ **Model Performance**: POOR - Requires significant retraining\n"
        
        report += """
### Recommended Hyperparameter Adjustments

#### If Exact Match Rate < 60% (Major Retraining Needed):
```python
training_args = TrainingArguments(
    learning_rate=3e-4,           # Increase from 5e-5
    num_train_epochs=5,           # Increase from 3
    per_device_train_batch_size=8, # Increase if memory allows
    warmup_steps=1000,            # Increase warmup
    weight_decay=0.01,            # Add regularization
    save_steps=500,               # More frequent saves
    eval_steps=500,               # More frequent evaluation
    logging_steps=100,
    gradient_accumulation_steps=2, # If batch size limited
    fp16=True,                    # Memory optimization
    dataloader_num_workers=4,
    remove_unused_columns=False,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    greater_is_better=False,
    save_total_limit=3,
    seed=42
)
```

#### If Exact Match Rate 60-80% (Fine-tuning Needed):
```python
training_args = TrainingArguments(
    learning_rate=1e-4,           # Moderate increase
    num_train_epochs=4,           # One additional epoch
    per_device_train_batch_size=8,
    warmup_steps=500,
    weight_decay=0.005,           # Light regularization
    save_steps=250,
    eval_steps=250,
    logging_steps=50,
    fp16=True,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    save_total_limit=2
)
```

#### If Exact Match Rate > 80% (Minor Optimization):
```python
# Current model is performing well. Consider:
# 1. Reducing learning rate to 3e-5 for stability
# 2. Adding early stopping to prevent overfitting
# 3. Experimenting with different generation parameters

generation_config = GenerationConfig(
    max_length=512,
    num_beams=4,                  # Good balance of quality/speed
    early_stopping=True,
    no_repeat_ngram_size=2,
    length_penalty=1.0,
    temperature=0.7               # For slight randomness
)
```

### Data Augmentation Recommendations
"""
        
        # Analyze which categories need more data
        small_categories = [cat for cat, stats in test_results['category_stats'].items() 
                          if stats['count'] < 10 or stats['exact_match_rate'] < 0.5]
        
        if small_categories:
            report += f"""
**Categories needing more training data**:
{', '.join(small_categories)}

**Suggested actions**:
1. Generate 50-100 additional examples for each weak category
2. Use data augmentation techniques (paraphrasing, synonym replacement)
3. Add more complex real-world scenarios
"""
        
        report += """
### Model Architecture Recommendations

#### Current T5 Model Assessment:
- **Model Size**: Appropriate for clinical domain
- **Architecture**: T5 is well-suited for text-to-text tasks

#### If Performance Issues Persist:
1. **Try T5-base** instead of T5-small (if using small)
2. **Consider domain-specific pre-training** on clinical texts
3. **Implement custom loss functions** for SQL syntax
4. **Add SQL validation during training** with penalty for invalid queries

### Generation Parameter Optimization
Based on benchmark results, recommended settings:
```python
# For Production (Best Quality)
generation_params = {
    "max_length": 512,
    "num_beams": 4,
    "early_stopping": True,
    "no_repeat_ngram_size": 2,
    "length_penalty": 1.0
}

# For Fast Inference (Good Quality)
generation_params = {
    "max_length": 512,
    "num_beams": 2,
    "early_stopping": True,
    "do_sample": False
}
```

## Next Steps

### Immediate Actions (This Week):
1. **Analyze failed examples** in detail to identify patterns
2. **Test model on real clinical scenarios** with domain experts
3. **Implement SQL validation** in the inference pipeline
4. **Create error handling** for malformed queries

### Short-term Improvements (Next 2 Weeks):
1. **Fine-tune with adjusted hyperparameters** based on performance
2. **Add more training data** for weak categories
3. **Implement query post-processing** to fix common errors
4. **Create evaluation metrics** specific to clinical queries

### Long-term Enhancements (Next Month):
1. **Deploy model** with monitoring and feedback collection
2. **Implement active learning** to improve on real user queries
3. **Add query explanation** capabilities
4. **Integrate with clinical database** for end-to-end testing

## Conclusion

"""
        
        if exact_match_rate >= 0.8:
            report += "🎉 **The model shows strong performance** and is ready for production deployment with monitoring."
        elif exact_match_rate >= 0.6:
            report += "⚠️ **The model shows moderate performance** and would benefit from hyperparameter tuning and additional training data."
        else:
            report += "🔧 **The model needs significant improvement** through retraining with adjusted hyperparameters and expanded dataset."
        
        report += f"""

**Overall Recommendation**: {'DEPLOY WITH MONITORING' if exact_match_rate >= 0.8 else 'RETRAIN WITH SUGGESTED HYPERPARAMETERS' if exact_match_rate >= 0.6 else 'MAJOR RETRAINING REQUIRED'}
"""
        
        print(report)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n📄 Evaluation report saved to: {output_path}")
        
        return report

def main():
    """Main testing function."""
    print("🚀 Starting T5 Clinical Model Testing...")
    
    # Initialize tester
    tester = ClinicalT5ModelTester()
    
    # Load model
    if not tester.load_model():
        print("❌ Failed to load model. Exiting.")
        return
    
    print("\n" + "="*60)
    
    # Test sample queries
    print("1️⃣ Testing sample queries...")
    sample_results = tester.test_sample_queries()
    
    print("\n" + "="*60)
    
    # Evaluate on test set
    print("2️⃣ Evaluating on test dataset...")
    test_results = tester.evaluate_on_test_set()
    
    print("\n" + "="*60)
    
    # Benchmark performance
    print("3️⃣ Benchmarking generation parameters...")
    benchmark_results = tester.benchmark_performance()
    
    print("\n" + "="*60)
    
    # Generate comprehensive report
    print("4️⃣ Generating evaluation report...")
    report_path = "d:/projects/healthca/models/trained/model_evaluation_report.md"
    tester.generate_evaluation_report(sample_results, test_results, benchmark_results, report_path)
    
    print("\n✅ Model testing complete!")
    print(f"📊 Overall Performance: {test_results['correct_predictions']}/{test_results['total_examples']} ({test_results['correct_predictions']/test_results['total_examples']*100:.1f}%) exact matches")
    print(f"📄 Detailed report saved to: {report_path}")

if __name__ == "__main__":
    main()