#!/usr/bin/env python3
"""
Script to compare the previous model vs current model performance
"""

import sys
import os
import json
import time
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from models.quick_model_test import QuickClinicalT5Tester

class ModelComparator:
    def __init__(self):
        self.previous_model_path = "d:/projects/healthca/models/trained/t5_clinical_model/final_model"
        self.current_model_path = "d:/projects/healthca/models/trained/t5_clinical_model/final model last"
        
        # Test queries for comparison
        self.test_queries = [
            "How many patients do we have?",
            "Show me all male patients",
            "Find all patients with diabetes",
            "What are the most common conditions?",
            "Which providers see the most patients?",
            "Find patients with both diabetes and hypertension",
            "What is the average cost per encounter?",
            "Show patients diagnosed in the last year",
            "List all medications for patient ID 123",
            "Find encounters with high costs"
        ]
    
    def test_model(self, model_path, model_name):
        """Test a single model and return results"""
        print(f"\n{'='*60}")
        print(f"🧪 Testing {model_name}")
        print(f"📁 Path: {model_path}")
        print(f"{'='*60}")
        
        # Initialize tester
        tester = QuickClinicalT5Tester(model_path=model_path)
        
        # Load model
        start_time = time.time()
        if not tester.load_model():
            return {
                "model_name": model_name,
                "model_path": model_path,
                "load_success": False,
                "error": "Failed to load model"
            }
        
        load_time = time.time() - start_time
        
        # Test individual queries
        results = {
            "model_name": model_name,
            "model_path": model_path,
            "load_success": True,
            "load_time": load_time,
            "model_size": tester.model.num_parameters(),
            "query_results": [],
            "performance_metrics": {}
        }
        
        print(f"✅ Model loaded in {load_time:.2f}s")
        print(f"📊 Model parameters: {tester.model.num_parameters():,}")
        
        # Test each query
        total_time = 0
        valid_queries = 0
        syntax_correct = 0
        schema_compliant = 0
        
        for i, query in enumerate(self.test_queries, 1):
            print(f"\n🔍 Testing {i}/{len(self.test_queries)}: {query}")
            
            start_time = time.time()
            try:
                generated_sql = tester.generate_sql(query)
                generation_time = time.time() - start_time
                total_time += generation_time
                
                # Basic validation
                is_valid = self.validate_sql_basic(generated_sql)
                has_correct_syntax = self.check_sql_syntax(generated_sql)
                uses_schema = "clinical_data." in generated_sql
                
                if is_valid:
                    valid_queries += 1
                if has_correct_syntax:
                    syntax_correct += 1
                if uses_schema:
                    schema_compliant += 1
                
                query_result = {
                    "query": query,
                    "generated_sql": generated_sql,
                    "generation_time": generation_time,
                    "is_valid": is_valid,
                    "has_correct_syntax": has_correct_syntax,
                    "uses_schema": uses_schema,
                    "length": len(generated_sql)
                }
                
                results["query_results"].append(query_result)
                
                print(f"   ⏱️  Time: {generation_time:.3f}s")
                print(f"   📝 SQL: {generated_sql[:100]}{'...' if len(generated_sql) > 100 else ''}")
                print(f"   ✅ Valid: {is_valid} | Syntax: {has_correct_syntax} | Schema: {uses_schema}")
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                query_result = {
                    "query": query,
                    "generated_sql": None,
                    "generation_time": 0,
                    "is_valid": False,
                    "has_correct_syntax": False,
                    "uses_schema": False,
                    "error": str(e)
                }
                results["query_results"].append(query_result)
        
        # Calculate performance metrics
        total_queries = len(self.test_queries)
        results["performance_metrics"] = {
            "total_queries": total_queries,
            "valid_queries": valid_queries,
            "syntax_correct": syntax_correct,
            "schema_compliant": schema_compliant,
            "validity_rate": (valid_queries / total_queries) * 100,
            "syntax_rate": (syntax_correct / total_queries) * 100,
            "schema_rate": (schema_compliant / total_queries) * 100,
            "avg_generation_time": total_time / total_queries if total_queries > 0 else 0,
            "total_generation_time": total_time
        }
        
        return results
    
    def validate_sql_basic(self, sql):
        """Basic SQL validation"""
        if not sql or not isinstance(sql, str):
            return False
        
        sql_upper = sql.upper().strip()
        
        # Must start with SELECT
        if not sql_upper.startswith('SELECT'):
            return False
        
        # Should not be just the question repeated
        if any(word in sql_upper for word in ['HOW MANY', 'SHOW ME', 'FIND ALL', 'WHAT ARE']):
            return False
        
        # Should not have excessive repetition
        words = sql.split()
        if len(words) > 3:
            # Check for repetitive patterns
            for i in range(len(words) - 2):
                if words[i] == words[i+1] == words[i+2]:
                    return False
        
        return True
    
    def check_sql_syntax(self, sql):
        """Check basic SQL syntax"""
        if not sql:
            return False
        
        sql_upper = sql.upper().strip()
        
        # Basic structure checks
        has_select = sql_upper.startswith('SELECT')
        has_from = 'FROM' in sql_upper
        balanced_parens = sql.count('(') == sql.count(')')
        
        return has_select and has_from and balanced_parens
    
    def compare_models(self):
        """Compare both models and generate report"""
        print("🔄 Starting Model Comparison")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test previous model
        previous_results = self.test_model(self.previous_model_path, "Previous Model (final_model)")
        
        # Test current model
        current_results = self.test_model(self.current_model_path, "Current Model (final model last)")
        
        # Generate comparison report
        report = self.generate_comparison_report(previous_results, current_results)
        
        # Save results
        comparison_data = {
            "timestamp": datetime.now().isoformat(),
            "previous_model": previous_results,
            "current_model": current_results,
            "comparison_report": report
        }
        
        # Save to JSON
        with open("d:/projects/healthca/model_comparison_results.json", "w", encoding="utf-8") as f:
            json.dump(comparison_data, f, indent=2, ensure_ascii=False)
        
        # Save report to markdown
        with open("d:/projects/healthca/model_comparison_report.md", "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"\n✅ Comparison complete!")
        print(f"📊 Results saved to: model_comparison_results.json")
        print(f"📝 Report saved to: model_comparison_report.md")
        
        return comparison_data
    
    def generate_comparison_report(self, previous, current):
        """Generate detailed comparison report"""
        
        # Handle case where models failed to load
        if not previous.get("load_success", False):
            prev_metrics = {"validity_rate": 0, "syntax_rate": 0, "schema_rate": 0, "avg_generation_time": 0}
        else:
            prev_metrics = previous["performance_metrics"]
        
        if not current.get("load_success", False):
            curr_metrics = {"validity_rate": 0, "syntax_rate": 0, "schema_rate": 0, "avg_generation_time": 0}
        else:
            curr_metrics = current["performance_metrics"]
        
        # Calculate improvements
        validity_improvement = curr_metrics["validity_rate"] - prev_metrics["validity_rate"]
        syntax_improvement = curr_metrics["syntax_rate"] - prev_metrics["syntax_rate"]
        schema_improvement = curr_metrics["schema_rate"] - prev_metrics["schema_rate"]
        speed_improvement = prev_metrics["avg_generation_time"] - curr_metrics["avg_generation_time"]
        
        report = f"""# 🔄 Model Comparison Report

## 📊 Performance Summary

| Metric | Previous Model | Current Model | Improvement |
|--------|----------------|---------------|-------------|
| **Validity Rate** | {prev_metrics['validity_rate']:.1f}% | {curr_metrics['validity_rate']:.1f}% | {validity_improvement:+.1f}% |
| **Syntax Correctness** | {prev_metrics['syntax_rate']:.1f}% | {curr_metrics['syntax_rate']:.1f}% | {syntax_improvement:+.1f}% |
| **Schema Compliance** | {prev_metrics['schema_rate']:.1f}% | {curr_metrics['schema_rate']:.1f}% | {schema_improvement:+.1f}% |
| **Avg Generation Time** | {prev_metrics['avg_generation_time']:.3f}s | {curr_metrics['avg_generation_time']:.3f}s | {speed_improvement:+.3f}s |

## 🎯 Overall Assessment

"""

        # Determine overall improvement
        if validity_improvement > 10 and syntax_improvement > 10:
            assessment = "🚀 **SIGNIFICANT IMPROVEMENT** - Current model shows major gains"
        elif validity_improvement > 0 and syntax_improvement > 0:
            assessment = "📈 **MODERATE IMPROVEMENT** - Current model is better"
        elif validity_improvement == 0 and syntax_improvement == 0:
            assessment = "➡️ **NO CHANGE** - Models perform similarly"
        elif validity_improvement < -10 or syntax_improvement < -10:
            assessment = "📉 **SIGNIFICANT REGRESSION** - Current model is much worse"
        else:
            assessment = "📉 **SLIGHT REGRESSION** - Current model is slightly worse"
        
        report += assessment + "\n\n"
        
        # Add detailed analysis
        report += "## 🔍 Detailed Analysis\n\n"
        
        if previous.get("load_success", False) and current.get("load_success", False):
            report += f"### Model Loading\n"
            report += f"- **Previous Model**: Loaded in {previous['load_time']:.2f}s\n"
            report += f"- **Current Model**: Loaded in {current['load_time']:.2f}s\n"
            report += f"- **Model Size**: {previous['model_size']:,} parameters\n\n"
            
            # Query-by-query comparison
            report += "### Query-by-Query Comparison\n\n"
            
            for i, query in enumerate(self.test_queries):
                prev_result = previous["query_results"][i] if i < len(previous["query_results"]) else {}
                curr_result = current["query_results"][i] if i < len(current["query_results"]) else {}
                
                report += f"#### Query {i+1}: {query}\n\n"
                
                if prev_result.get("generated_sql") and curr_result.get("generated_sql"):
                    report += f"**Previous Model Output:**\n```sql\n{prev_result['generated_sql']}\n```\n\n"
                    report += f"**Current Model Output:**\n```sql\n{curr_result['generated_sql']}\n```\n\n"
                    
                    # Compare metrics
                    prev_valid = prev_result.get("is_valid", False)
                    curr_valid = curr_result.get("is_valid", False)
                    
                    if curr_valid and not prev_valid:
                        report += "✅ **IMPROVEMENT**: Current model generates valid SQL\n\n"
                    elif prev_valid and not curr_valid:
                        report += "❌ **REGRESSION**: Previous model was better\n\n"
                    elif curr_valid and prev_valid:
                        report += "✅ **BOTH VALID**: Both models generate valid SQL\n\n"
                    else:
                        report += "❌ **BOTH INVALID**: Neither model generates valid SQL\n\n"
                
                report += "---\n\n"
        
        else:
            if not previous.get("load_success", False):
                report += "❌ **Previous model failed to load**\n\n"
            if not current.get("load_success", False):
                report += "❌ **Current model failed to load**\n\n"
        
        # Recommendations
        report += "## 🎯 Recommendations\n\n"
        
        if validity_improvement > 0:
            report += "✅ **Use Current Model**: Shows improvement over previous version\n\n"
        elif validity_improvement < -5:
            report += "⚠️ **Revert to Previous Model**: Current model shows significant regression\n\n"
        else:
            report += "🔄 **Further Training Needed**: Both models need improvement\n\n"
        
        report += f"**Generated on**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return report

def main():
    comparator = ModelComparator()
    results = comparator.compare_models()
    
    # Print summary
    print("\n" + "="*60)
    print("📊 COMPARISON SUMMARY")
    print("="*60)
    
    if results["previous_model"].get("load_success") and results["current_model"].get("load_success"):
        prev_metrics = results["previous_model"]["performance_metrics"]
        curr_metrics = results["current_model"]["performance_metrics"]
        
        print(f"Previous Model Validity: {prev_metrics['validity_rate']:.1f}%")
        print(f"Current Model Validity:  {curr_metrics['validity_rate']:.1f}%")
        print(f"Improvement: {curr_metrics['validity_rate'] - prev_metrics['validity_rate']:+.1f}%")
    else:
        print("❌ One or both models failed to load")

if __name__ == "__main__":
    main()