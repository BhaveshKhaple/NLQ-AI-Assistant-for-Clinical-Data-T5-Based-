#!/usr/bin/env python3
"""
Dataset Merger and Validator
Merges all generated datasets into a single comprehensive dataset and validates quality.
"""

import json
import os
import shutil
from datetime import datetime
from typing import List, Dict, Set
import re

class DatasetMerger:
    def __init__(self):
        self.base_path = "d:/projects/healthca/data/processed"
        self.output_path = f"{self.base_path}/final_merged_dataset"
        
        # Dataset directories to merge
        self.dataset_dirs = [
            "final_10k_dataset",
            "comprehensive_dataset", 
            "large_dataset",
            "clean_dataset",
            "10k_dataset"
        ]
        
        # Files to clean up after merging
        self.cleanup_files = [
            "clinical_nlq_training_data.json",
            "test_data.json",
            "train_data.json", 
            "val_data.json",
            "colab_loader_example.py",
            "validation_report.md"
        ]

    def load_dataset_files(self, dataset_dir: str) -> Dict[str, List[Dict]]:
        """Load train, val, test files from a dataset directory."""
        dataset_path = f"{self.base_path}/{dataset_dir}"
        data = {"train": [], "val": [], "test": []}
        
        if not os.path.exists(dataset_path):
            print(f"   ⚠️  Dataset directory not found: {dataset_dir}")
            return data
            
        for split in ["train", "val", "test"]:
            file_path = f"{dataset_path}/{split}_data.json"
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        split_data = json.load(f)
                        if isinstance(split_data, list):
                            data[split] = split_data
                        else:
                            print(f"   ⚠️  Invalid format in {file_path}")
                except Exception as e:
                    print(f"   ❌ Error loading {file_path}: {e}")
            else:
                print(f"   ⚠️  File not found: {file_path}")
        
        return data

    def validate_example(self, example: Dict) -> bool:
        """Validate a single training example."""
        # Check required fields
        if not isinstance(example, dict):
            return False
            
        if "input_text" not in example or "target_text" not in example:
            return False
            
        input_text = example["input_text"]
        target_text = example["target_text"]
        
        # Check for empty or invalid content
        if not input_text or not target_text:
            return False
            
        if not isinstance(input_text, str) or not isinstance(target_text, str):
            return False
            
        # Check input format
        if not input_text.startswith("translate to sql:"):
            return False
            
        # Check SQL validity (basic)
        sql_upper = target_text.upper().strip()
        if not sql_upper.startswith("SELECT"):
            return False
            
        # Check for schema context
        if "Database Schema:" not in input_text:
            return False
            
        return True

    def deduplicate_examples(self, examples: List[Dict]) -> List[Dict]:
        """Remove duplicate examples based on input text."""
        seen_inputs = set()
        unique_examples = []
        
        for example in examples:
            # Create a normalized key for deduplication
            input_key = example["input_text"].split("Database Schema:")[0].strip().lower()
            
            if input_key not in seen_inputs:
                seen_inputs.add(input_key)
                unique_examples.append(example)
        
        return unique_examples

    def merge_all_datasets(self) -> Dict[str, List[Dict]]:
        """Merge all datasets into a single comprehensive dataset."""
        print("🔄 Merging all datasets...")
        
        all_data = {"train": [], "val": [], "test": []}
        dataset_stats = {}
        
        for dataset_dir in self.dataset_dirs:
            print(f"   📂 Processing {dataset_dir}...")
            data = self.load_dataset_files(dataset_dir)
            
            stats = {}
            for split in ["train", "val", "test"]:
                valid_examples = [ex for ex in data[split] if self.validate_example(ex)]
                all_data[split].extend(valid_examples)
                stats[split] = len(valid_examples)
            
            dataset_stats[dataset_dir] = stats
            total = sum(stats.values())
            print(f"      ✅ Added {total} valid examples (train: {stats['train']}, val: {stats['val']}, test: {stats['test']})")
        
        # Deduplicate within each split
        print("\n🔄 Deduplicating examples...")
        for split in ["train", "val", "test"]:
            before_count = len(all_data[split])
            all_data[split] = self.deduplicate_examples(all_data[split])
            after_count = len(all_data[split])
            removed = before_count - after_count
            print(f"   {split}: {before_count} → {after_count} (removed {removed} duplicates)")
        
        return all_data, dataset_stats

    def validate_merged_dataset(self, data: Dict[str, List[Dict]]) -> Dict:
        """Validate the merged dataset quality."""
        print("\n🔍 Validating merged dataset...")
        
        validation_results = {
            "total_examples": sum(len(data[split]) for split in data),
            "splits": {split: len(data[split]) for split in data},
            "validation_errors": [],
            "sql_patterns": {},
            "data_leakage": False
        }
        
        # Check for data leakage between splits
        train_inputs = set(ex["input_text"].split("Database Schema:")[0].strip().lower() for ex in data["train"])
        val_inputs = set(ex["input_text"].split("Database Schema:")[0].strip().lower() for ex in data["val"])
        test_inputs = set(ex["input_text"].split("Database Schema:")[0].strip().lower() for ex in data["test"])
        
        train_val_overlap = len(train_inputs.intersection(val_inputs))
        train_test_overlap = len(train_inputs.intersection(test_inputs))
        val_test_overlap = len(val_inputs.intersection(test_inputs))
        
        if train_val_overlap > 0 or train_test_overlap > 0 or val_test_overlap > 0:
            validation_results["data_leakage"] = True
            validation_results["validation_errors"].append(
                f"Data leakage detected: train-val: {train_val_overlap}, train-test: {train_test_overlap}, val-test: {val_test_overlap}"
            )
        
        # Analyze SQL patterns
        sql_patterns = {}
        for split in data:
            for example in data[split]:
                sql = example["target_text"].upper()
                
                # Count SQL patterns
                if "JOIN" in sql:
                    sql_patterns["joins"] = sql_patterns.get("joins", 0) + 1
                if "GROUP BY" in sql:
                    sql_patterns["group_by"] = sql_patterns.get("group_by", 0) + 1
                if "HAVING" in sql:
                    sql_patterns["having"] = sql_patterns.get("having", 0) + 1
                if "COUNT(" in sql:
                    sql_patterns["aggregation"] = sql_patterns.get("aggregation", 0) + 1
                if "WHERE" in sql:
                    sql_patterns["filtering"] = sql_patterns.get("filtering", 0) + 1
        
        validation_results["sql_patterns"] = sql_patterns
        
        # Sample validation
        sample_errors = 0
        for split in data:
            for i, example in enumerate(data[split][:100]):  # Check first 100 of each split
                if not self.validate_example(example):
                    sample_errors += 1
                    if len(validation_results["validation_errors"]) < 10:  # Limit error messages
                        validation_results["validation_errors"].append(
                            f"Invalid example in {split}[{i}]: {str(example)[:100]}..."
                        )
        
        validation_results["sample_error_rate"] = sample_errors / min(300, validation_results["total_examples"])
        
        return validation_results

    def save_merged_dataset(self, data: Dict[str, List[Dict]], validation_results: Dict, dataset_stats: Dict):
        """Save the merged and validated dataset."""
        print(f"\n💾 Saving merged dataset to {self.output_path}")
        
        # Create output directory
        os.makedirs(self.output_path, exist_ok=True)
        
        # Save data files
        for split in data:
            file_path = f"{self.output_path}/{split}_data.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data[split], f, indent=2, ensure_ascii=False)
            print(f"   ✅ Saved {len(data[split])} examples to {split}_data.json")
        
        # Create comprehensive metadata
        metadata = {
            "name": "Clinical NLQ Merged Training Dataset",
            "description": "Comprehensive merged dataset from all generated training data",
            "version": "7.0",
            "created_date": datetime.now().isoformat(),
            "total_examples": validation_results["total_examples"],
            "splits": validation_results["splits"],
            "source_datasets": dataset_stats,
            "validation_results": validation_results,
            "database_schema": "clinical_data (PostgreSQL)",
            "format": "seq2seq with schema context",
            "quality_metrics": {
                "data_leakage": validation_results["data_leakage"],
                "sample_error_rate": validation_results["sample_error_rate"],
                "sql_pattern_coverage": len(validation_results["sql_patterns"])
            }
        }
        
        with open(f"{self.output_path}/metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # Create validation report
        report = f"""# Clinical NLQ Dataset Validation Report

## Dataset Summary
- **Total Examples**: {validation_results['total_examples']:,}
- **Train**: {validation_results['splits']['train']:,}
- **Validation**: {validation_results['splits']['val']:,}
- **Test**: {validation_results['splits']['test']:,}

## Quality Metrics
- **Data Leakage**: {'❌ DETECTED' if validation_results['data_leakage'] else '✅ NONE'}
- **Sample Error Rate**: {validation_results['sample_error_rate']:.2%}

## SQL Pattern Coverage
"""
        for pattern, count in validation_results["sql_patterns"].items():
            report += f"- **{pattern.title()}**: {count:,} examples\n"
        
        report += f"""
## Source Dataset Contributions
"""
        for dataset, stats in dataset_stats.items():
            total = sum(stats.values())
            report += f"- **{dataset}**: {total:,} examples\n"
        
        if validation_results["validation_errors"]:
            report += f"""
## Validation Errors
"""
            for error in validation_results["validation_errors"][:10]:
                report += f"- {error}\n"
        
        with open(f"{self.output_path}/validation_report.md", 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"   ✅ Saved metadata and validation report")

    def cleanup_old_files(self):
        """Remove unnecessary files and directories."""
        print("\n🧹 Cleaning up unnecessary files...")
        
        # Remove old dataset directories
        for dataset_dir in self.dataset_dirs:
            dir_path = f"{self.base_path}/{dataset_dir}"
            if os.path.exists(dir_path) and dataset_dir != "final_merged_dataset":
                try:
                    shutil.rmtree(dir_path)
                    print(f"   🗑️  Removed directory: {dataset_dir}")
                except Exception as e:
                    print(f"   ⚠️  Could not remove {dataset_dir}: {e}")
        
        # Remove old files
        for file_name in self.cleanup_files:
            file_path = f"{self.base_path}/{file_name}"
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"   🗑️  Removed file: {file_name}")
                except Exception as e:
                    print(f"   ⚠️  Could not remove {file_name}: {e}")

    def create_colab_loader(self):
        """Create a simple loader script for Google Colab."""
        colab_script = '''"""
Clinical NLQ Dataset Loader for Google Colab
Load the merged training dataset for T5 model training.
"""

import json
import requests
from typing import Dict, List

def load_clinical_nlq_dataset(base_url: str = None) -> Dict[str, List[Dict]]:
    """
    Load the clinical NLQ training dataset.
    
    Args:
        base_url: Base URL where dataset files are hosted (optional)
    
    Returns:
        Dictionary with 'train', 'val', 'test' splits
    """
    
    # If running locally, load from files
    if base_url is None:
        try:
            dataset = {}
            for split in ['train', 'val', 'test']:
                with open(f'{split}_data.json', 'r') as f:
                    dataset[split] = json.load(f)
            return dataset
        except FileNotFoundError:
            print("Dataset files not found locally. Please provide base_url or upload files.")
            return {"train": [], "val": [], "test": []}
    
    # Load from URL
    dataset = {}
    for split in ['train', 'val', 'test']:
        try:
            url = f"{base_url}/{split}_data.json"
            response = requests.get(url)
            response.raise_for_status()
            dataset[split] = response.json()
            print(f"Loaded {len(dataset[split])} {split} examples")
        except Exception as e:
            print(f"Error loading {split} data: {e}")
            dataset[split] = []
    
    return dataset

def validate_dataset(dataset: Dict[str, List[Dict]]) -> None:
    """Validate the loaded dataset."""
    total = sum(len(dataset[split]) for split in dataset)
    print(f"\\nDataset Summary:")
    print(f"  Total examples: {total:,}")
    for split in ['train', 'val', 'test']:
        print(f"  {split.capitalize()}: {len(dataset[split]):,}")
    
    # Check format
    if total > 0:
        example = None
        for split in dataset:
            if dataset[split]:
                example = dataset[split][0]
                break
        
        if example:
            required_fields = ['input_text', 'target_text']
            missing_fields = [field for field in required_fields if field not in example]
            if missing_fields:
                print(f"  ⚠️  Missing fields: {missing_fields}")
            else:
                print(f"  ✅ Format validation passed")

# Example usage:
if __name__ == "__main__":
    # Load dataset
    dataset = load_clinical_nlq_dataset()
    
    # Validate
    validate_dataset(dataset)
    
    # Show sample
    if dataset['train']:
        print(f"\\nSample training example:")
        example = dataset['train'][0]
        print(f"Input: {example['input_text'][:100]}...")
        print(f"Target: {example['target_text'][:100]}...")
'''
        
        with open(f"{self.output_path}/colab_loader.py", 'w', encoding='utf-8') as f:
            f.write(colab_script)
        
        print(f"   ✅ Created colab_loader.py")

def main():
    """Main function to merge and validate datasets."""
    print("🚀 Clinical NLQ Dataset Merger and Validator")
    print("=" * 60)
    
    merger = DatasetMerger()
    
    # Merge all datasets
    merged_data, dataset_stats = merger.merge_all_datasets()
    
    # Validate merged dataset
    validation_results = merger.validate_merged_dataset(merged_data)
    
    # Save merged dataset
    merger.save_merged_dataset(merged_data, validation_results, dataset_stats)
    
    # Create Colab loader
    merger.create_colab_loader()
    
    # Clean up old files
    merger.cleanup_old_files()
    
    # Final summary
    print(f"\n🎉 Dataset merging complete!")
    print(f"📊 Final dataset statistics:")
    print(f"   Total examples: {validation_results['total_examples']:,}")
    print(f"   Train: {validation_results['splits']['train']:,}")
    print(f"   Validation: {validation_results['splits']['val']:,}")
    print(f"   Test: {validation_results['splits']['test']:,}")
    print(f"   Data leakage: {'❌ DETECTED' if validation_results['data_leakage'] else '✅ NONE'}")
    print(f"   Error rate: {validation_results['sample_error_rate']:.2%}")
    print(f"\n📁 Final dataset location: {merger.output_path}")
    print(f"🎯 Ready for training in Google Colab!")

if __name__ == "__main__":
    main()