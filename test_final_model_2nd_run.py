#!/usr/bin/env python3
"""
Test the Final Model 2nd Run
Comprehensive testing of the model saved in 'models/trained/t5_clinical_model/final model 2nd run'
"""

import json
import torch
import time
import re
from typing import List, Dict, Tuple, Optional
from transformers import T5ForConditionalGeneration, AutoTokenizer
from collections import defaultdict
import pandas as pd
from datetime import datetime

class FinalModel2ndRunTester:
    def __init__(self):
        """Initialize the model tester with the final model 2nd run."""
        self.model_path = "d:/projects/healthca/models/trained/t5_clinical_model/final model 2nd run"
        self.model = None
        self.tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        print(f"🔧 Using device: {self.device}")
        print(f"📁 Model path: {self.model_path}")
        
    def load_model(self) -> bool:
        """Load the trained T5 model and tokenizer."""
        try:
            print(f"📥 Loading model from: {self.model_path}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
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
        
        # Add schema context to match training format
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
        
        # Format input to match training format
        input_text = f"translate to sql: {nlq} {schema_context}"
        
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
    
    def test_clinical_queries(self) -> List[Dict]:
        """Test the model with clinical-specific queries."""
        print("🧪 Testing model with clinical queries...")
        
        clinical_queries = [
            # Basic patient queries
            {
                "nlq": "How many patients do we have?",
                "category": "basic_count",
                "expected_pattern": ["COUNT", "patients"]
            },
            {
                "nlq": "List all male patients",
                "category": "basic_filter",
                "expected_pattern": ["SELECT", "patients", "WHERE", "gender"]
            },
            {
                "nlq": "Show patients from Massachusetts",
                "category": "location_filter",
                "expected_pattern": ["SELECT", "patients", "WHERE", "state"]
            },
            
            # Condition-based queries
            {
                "nlq": "Find patients with diabetes",
                "category": "condition_search",
                "expected_pattern": ["JOIN", "conditions", "diabetes"]
            },
            {
                "nlq": "List patients with hypertension",
                "category": "condition_search",
                "expected_pattern": ["JOIN", "conditions", "hypertension"]
            },
            {
                "nlq": "Show patients with both diabetes and hypertension",
                "category": "complex_condition",
                "expected_pattern": ["JOIN", "conditions", "diabetes", "hypertension"]
            },
            
            # Medication queries
            {
                "nlq": "Find patients taking insulin",
                "category": "medication_search",
                "expected_pattern": ["JOIN", "medications", "insulin"]
            },
            {
                "nlq": "List all medications prescribed",
                "category": "medication_list",
                "expected_pattern": ["SELECT", "medications", "description"]
            },
            {
                "nlq": "Show patients on multiple medications",
                "category": "complex_medication",
                "expected_pattern": ["COUNT", "medications", "GROUP BY"]
            },
            
            # Provider queries
            {
                "nlq": "List all healthcare providers",
                "category": "provider_list",
                "expected_pattern": ["SELECT", "providers"]
            },
            {
                "nlq": "Find cardiologists",
                "category": "specialty_search",
                "expected_pattern": ["SELECT", "providers", "WHERE", "speciality"]
            },
            
            # Financial queries
            {
                "nlq": "Show high-cost patients",
                "category": "financial_analysis",
                "expected_pattern": ["SELECT", "patients", "healthcare_expenses"]
            },
            {
                "nlq": "Calculate average healthcare costs",
                "category": "financial_aggregation",
                "expected_pattern": ["AVG", "healthcare_expenses"]
            },
            
            # Temporal queries
            {
                "nlq": "Find recent patient visits",
                "category": "temporal_analysis",
                "expected_pattern": ["SELECT", "encounters", "start_date"]
            },
            {
                "nlq": "Show patients diagnosed this year",
                "category": "temporal_filter",
                "expected_pattern": ["WHERE", "start_date", "EXTRACT"]
            }
        ]
        
        results = []
        
        for i, query in enumerate(clinical_queries):
            print(f"  Testing query {i+1}/{len(clinical_queries)}: {query['nlq'][:50]}...")
            
            start_time = time.time()
            generated_sql = self.generate_sql(query['nlq'])
            generation_time = time.time() - start_time
            
            # Analyze the generated SQL
            sql_upper = generated_sql.upper()
            
            result = {
                'nlq': query['nlq'],
                'generated_sql': generated_sql,
                'category': query['category'],
                'expected_pattern': query['expected_pattern'],
                'generation_time': generation_time,
                'sql_length': len(generated_sql),
                'analysis': {
                    'has_clinical_data_schema': 'clinical_data.' in generated_sql,
                    'has_select': sql_upper.startswith('SELECT'),
                    'has_from': 'FROM' in sql_upper,
                    'has_where': 'WHERE' in sql_upper,
                    'has_join': 'JOIN' in sql_upper,
                    'has_group_by': 'GROUP BY' in sql_upper,
                    'has_order_by': 'ORDER BY' in sql_upper,
                    'has_count': 'COUNT' in sql_upper,
                    'has_avg': 'AVG' in sql_upper,
                    'pattern_match_score': self.calculate_pattern_match(generated_sql, query['expected_pattern'])
                }
            }
            
            results.append(result)
        
        return results
    
    def calculate_pattern_match(self, sql: str, expected_patterns: List[str]) -> float:
        """Calculate how well the generated SQL matches expected patterns."""
        sql_upper = sql.upper()
        matches = 0
        
        for pattern in expected_patterns:
            if pattern.upper() in sql_upper:
                matches += 1
        
        return matches / len(expected_patterns) if expected_patterns else 0.0
    
    def evaluate_on_test_set(self) -> Dict:
        """Evaluate the model on the test dataset."""
        print("📊 Evaluating model on test dataset...")
        
        # Try to load test data from the validated dataset
        test_data_path = "d:/projects/healthca/data/processed/final_merged_dataset/test_data.json"
        
        try:
            with open(test_data_path, 'r', encoding='utf-8') as f:
                test_data = json.load(f)
        except FileNotFoundError:
            print(f"❌ Test data not found at {test_data_path}")
            return {"error": "Test data not found"}
        
        print(f"📋 Loaded {len(test_data)} test examples")
        
        results = {
            'total_examples': len(test_data),
            'correct_predictions': 0,
            'partial_matches': 0,
            'syntax_correct': 0,
            'schema_correct': 0,
            'avg_generation_time': 0,
            'detailed_results': []
        }
        
        total_time = 0
        
        # Test on a subset for faster evaluation
        test_subset = test_data[:50]  # Test first 50 examples
        print(f"📋 Testing on subset of {len(test_subset)} examples for faster evaluation")
        
        for i, example in enumerate(test_subset):
            if i % 10 == 0:
                print(f"  Progress: {i}/{len(test_subset)} ({i/len(test_subset)*100:.1f}%)")
            
            # Extract NLQ from input_text
            nlq = example['input_text'].split('Database Schema:')[0].replace('translate to sql: ', '').strip()
            expected_sql = example['target_text']
            
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
                'generation_time': generation_time,
                **evaluation
            }
            
            results['detailed_results'].append(detailed_result)
            
            # Update counters
            if evaluation['exact_match']:
                results['correct_predictions'] += 1
            if evaluation['partial_match']:
                results['partial_matches'] += 1
            if evaluation['syntax_correct']:
                results['syntax_correct'] += 1
            if evaluation['schema_correct']:
                results['schema_correct'] += 1
        
        results['avg_generation_time'] = total_time / len(test_subset)
        results['total_examples'] = len(test_subset)  # Update to reflect actual tested examples
        
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
            partial_match = overlap > 0.6  # 60% word overlap
        
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
    
    def generate_test_report(self, clinical_results: List[Dict], test_results: Dict) -> str:
        """Generate a comprehensive test report."""
        
        report = f"""
# Final Model 2nd Run - Test Report

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

## Clinical Query Test Results

"""
        
        # Group clinical results by category
        category_results = defaultdict(list)
        for result in clinical_results:
            category_results[result['category']].append(result)
        
        for category, results in category_results.items():
            avg_pattern_score = sum(r['analysis']['pattern_match_score'] for r in results) / len(results)
            schema_compliance = sum(1 for r in results if r['analysis']['has_clinical_data_schema']) / len(results)
            
            report += f"""
### {category.replace('_', ' ').title()}
- **Examples**: {len(results)}
- **Average Pattern Match**: {avg_pattern_score:.1%}
- **Schema Compliance**: {schema_compliance:.1%}
"""
        
        report += """
## Sample Generated Queries

"""
        
        # Show best and worst examples
        clinical_results_sorted = sorted(clinical_results, key=lambda x: x['analysis']['pattern_match_score'], reverse=True)
        
        report += "### Best Performing Queries\n"
        for i, result in enumerate(clinical_results_sorted[:3], 1):
            report += f"""
#### Example {i}
**Question**: {result['nlq']}
**Generated SQL**: 
```sql
{result['generated_sql']}
```
**Pattern Match Score**: {result['analysis']['pattern_match_score']:.1%}
**Generation Time**: {result['generation_time']:.3f}s
"""
        
        report += "\n### Challenging Queries\n"
        for i, result in enumerate(clinical_results_sorted[-3:], 1):
            report += f"""
#### Example {i}
**Question**: {result['nlq']}
**Generated SQL**: 
```sql
{result['generated_sql']}
```
**Pattern Match Score**: {result['analysis']['pattern_match_score']:.1%}
**Issues**: {', '.join([k for k, v in result['analysis'].items() if k.startswith('has_') and not v])}
"""
        
        # Performance assessment
        exact_match_rate = test_results['correct_predictions'] / test_results['total_examples']
        syntax_rate = test_results['syntax_correct'] / test_results['total_examples']
        schema_rate = test_results['schema_correct'] / test_results['total_examples']
        
        report += f"""
## Performance Assessment

### Model Quality: """
        
        if exact_match_rate >= 0.8 and syntax_rate >= 0.95 and schema_rate >= 0.95:
            report += "🎉 **EXCELLENT** - Ready for production"
        elif exact_match_rate >= 0.6 and syntax_rate >= 0.9 and schema_rate >= 0.9:
            report += "✅ **GOOD** - Minor improvements needed"
        elif exact_match_rate >= 0.4 and syntax_rate >= 0.8:
            report += "⚠️ **MODERATE** - Needs improvement"
        else:
            report += "❌ **POOR** - Requires significant work"
        
        report += f"""

### Key Metrics
- **Exact Match Rate**: {exact_match_rate:.1%}
- **Syntax Correctness**: {syntax_rate:.1%}
- **Schema Compliance**: {schema_rate:.1%}
- **Average Generation Speed**: {test_results['avg_generation_time']:.3f}s per query

### Strengths
"""
        
        if schema_rate >= 0.9:
            report += "- ✅ **Excellent schema compliance** - Model correctly uses clinical_data prefix\n"
        if syntax_rate >= 0.9:
            report += "- ✅ **High syntax correctness** - Generates valid SQL queries\n"
        if test_results['avg_generation_time'] < 1.0:
            report += "- ✅ **Fast generation** - Suitable for real-time applications\n"
        
        report += "\n### Areas for Improvement\n"
        
        if exact_match_rate < 0.8:
            report += f"- 🔧 **Exact match rate** could be improved from {exact_match_rate:.1%}\n"
        if syntax_rate < 0.95:
            report += f"- 🔧 **SQL syntax** needs improvement from {syntax_rate:.1%}\n"
        if schema_rate < 0.95:
            report += f"- 🔧 **Schema compliance** needs improvement from {schema_rate:.1%}\n"
        
        report += """
## Recommendations

### Immediate Actions
1. **Deploy for testing** with clinical domain experts
2. **Implement SQL validation** in the inference pipeline
3. **Add error handling** for malformed queries
4. **Monitor performance** on real clinical scenarios

### Future Improvements
1. **Fine-tune** on additional clinical data if needed
2. **Add query explanation** capabilities
3. **Implement feedback loop** for continuous improvement
4. **Optimize generation parameters** for better performance

## Conclusion

"""
        
        if exact_match_rate >= 0.7:
            report += "🎯 **The Final Model 2nd Run shows strong performance** and demonstrates significant improvement in clinical NLQ-to-SQL conversion. The model is ready for deployment with appropriate monitoring."
        else:
            report += "🔧 **The Final Model 2nd Run shows moderate performance** and would benefit from additional fine-tuning or training data augmentation."
        
        return report

def main():
    """Main testing function for Final Model 2nd Run."""
    print("🚀 Testing Final Model 2nd Run...")
    print("=" * 60)
    
    # Initialize tester
    tester = FinalModel2ndRunTester()
    
    # Load model
    if not tester.load_model():
        print("❌ Failed to load model. Exiting.")
        return
    
    print("\n" + "="*60)
    
    # Test clinical queries
    print("1️⃣ Testing clinical queries...")
    clinical_results = tester.test_clinical_queries()
    
    print("\n" + "="*60)
    
    # Evaluate on test set
    print("2️⃣ Evaluating on test dataset...")
    test_results = tester.evaluate_on_test_set()
    
    if "error" in test_results:
        print("❌ Could not evaluate on test set")
        return
    
    print("\n" + "="*60)
    
    # Generate report
    print("3️⃣ Generating test report...")
    report = tester.generate_test_report(clinical_results, test_results)
    
    # Save report
    report_path = "d:/projects/healthca/FINAL_MODEL_2ND_RUN_TEST_REPORT.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(report)
    print(f"\n📄 Test report saved to: {report_path}")
    
    print("\n✅ Final Model 2nd Run testing complete!")
    print(f"📊 Overall Performance: {test_results['correct_predictions']}/{test_results['total_examples']} ({test_results['correct_predictions']/test_results['total_examples']*100:.1f}%) exact matches")

if __name__ == "__main__":
    main()