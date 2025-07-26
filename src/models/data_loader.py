#!/usr/bin/env python3
"""
Clinical NLQ Training Data Loader
Simple utility to load the generated training dataset for T5 model training.
"""

import json
import pandas as pd
from typing import Dict, List, Tuple
from sklearn.model_selection import train_test_split

def load_clinical_nlq_dataset(file_path: str = "d:/projects/healthca/data/processed/clinical_nlq_training_data.json") -> Dict:
    """
    Load the clinical NLQ training dataset from JSON file.
    
    Args:
        file_path: Path to the JSON dataset file
        
    Returns:
        Dictionary containing metadata and data
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    print(f"✅ Loaded {dataset['metadata']['total_examples']} training examples")
    print(f"📊 Dataset: {dataset['metadata']['name']} v{dataset['metadata']['version']}")
    
    return dataset

def get_training_data(dataset: Dict) -> List[Dict]:
    """
    Extract just the training data from the dataset.
    
    Args:
        dataset: Full dataset dictionary
        
    Returns:
        List of training examples
    """
    return dataset['data']

def create_train_val_test_split(data: List[Dict], 
                               train_size: float = 0.7, 
                               val_size: float = 0.15, 
                               test_size: float = 0.15,
                               random_state: int = 42) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Split the data into train, validation, and test sets.
    
    Args:
        data: List of training examples
        train_size: Proportion for training set
        val_size: Proportion for validation set  
        test_size: Proportion for test set
        random_state: Random seed for reproducibility
        
    Returns:
        Tuple of (train_data, val_data, test_data)
    """
    assert abs(train_size + val_size + test_size - 1.0) < 1e-6, "Split sizes must sum to 1.0"
    
    # First split: train vs (val + test)
    train_data, temp_data = train_test_split(
        data, 
        test_size=(val_size + test_size), 
        random_state=random_state,
        stratify=[item['category'] for item in data]  # Stratify by category
    )
    
    # Second split: val vs test
    val_data, test_data = train_test_split(
        temp_data,
        test_size=(test_size / (val_size + test_size)),
        random_state=random_state,
        stratify=[item['category'] for item in temp_data]
    )
    
    print(f"📊 Data split:")
    print(f"  Training: {len(train_data)} examples ({len(train_data)/len(data)*100:.1f}%)")
    print(f"  Validation: {len(val_data)} examples ({len(val_data)/len(data)*100:.1f}%)")
    print(f"  Test: {len(test_data)} examples ({len(test_data)/len(data)*100:.1f}%)")
    
    return train_data, val_data, test_data

def format_for_t5(data: List[Dict], include_schema: bool = True) -> List[Dict]:
    """
    Format the data for T5 training with proper input/target structure.
    
    Args:
        data: List of training examples
        include_schema: Whether to include schema context in input
        
    Returns:
        List of formatted examples for T5
    """
    schema_context = """
    Database Schema: clinical_data
    Tables: patients, organizations, providers, encounters, conditions, medications, procedures, observations, immunizations, allergies, care_plans, payers
    Key relationships: patients.id -> conditions.patient_id, encounters.patient_id, medications.patient_id
    """ if include_schema else ""
    
    formatted_data = []
    for item in data:
        if include_schema:
            input_text = f"translate to sql: {item['nlq']} {schema_context.strip()}"
        else:
            input_text = f"translate to sql: {item['nlq']}"
            
        formatted_item = {
            "input_text": input_text,
            "target_text": item['sql'],
            "category": item['category'],
            "original_nlq": item['nlq']
        }
        formatted_data.append(formatted_item)
    
    return formatted_data

def save_splits_to_json(train_data: List[Dict], 
                       val_data: List[Dict], 
                       test_data: List[Dict],
                       output_dir: str = "d:/projects/healthca/data/processed/"):
    """
    Save the train/val/test splits to separate JSON files.
    
    Args:
        train_data: Training examples
        val_data: Validation examples  
        test_data: Test examples
        output_dir: Directory to save files
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # Save splits
    with open(f"{output_dir}/train_data.json", 'w', encoding='utf-8') as f:
        json.dump(train_data, f, indent=2, ensure_ascii=False)
    
    with open(f"{output_dir}/val_data.json", 'w', encoding='utf-8') as f:
        json.dump(val_data, f, indent=2, ensure_ascii=False)
        
    with open(f"{output_dir}/test_data.json", 'w', encoding='utf-8') as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved data splits to {output_dir}")

def get_category_distribution(data: List[Dict]) -> Dict[str, int]:
    """
    Get the distribution of categories in the dataset.
    
    Args:
        data: List of training examples
        
    Returns:
        Dictionary with category counts
    """
    categories = {}
    for item in data:
        category = item['category']
        categories[category] = categories.get(category, 0) + 1
    
    return categories

def print_dataset_stats(dataset: Dict):
    """
    Print comprehensive statistics about the dataset.
    
    Args:
        dataset: Full dataset dictionary
    """
    metadata = dataset['metadata']
    data = dataset['data']
    
    print(f"\n📊 Dataset Statistics:")
    print(f"  Name: {metadata['name']}")
    print(f"  Version: {metadata['version']}")
    print(f"  Created: {metadata['created_date']}")
    print(f"  Total Examples: {metadata['total_examples']}")
    print(f"  Database Schema: {metadata['database_schema']}")
    
    print(f"\n📈 Category Distribution:")
    for category, count in sorted(metadata['categories'].items()):
        percentage = (count / metadata['total_examples']) * 100
        print(f"  {category}: {count} ({percentage:.1f}%)")
    
    print(f"\n🎯 Target Distribution:")
    for dist_type, percentage in metadata['distribution'].items():
        print(f"  {dist_type}: {percentage}")

# Example usage for Colab/Jupyter
def load_for_colab_training():
    """
    Convenience function to load and prepare data for Colab training.
    Returns formatted data ready for T5 training.
    """
    # Load dataset
    dataset = load_clinical_nlq_dataset()
    
    # Print stats
    print_dataset_stats(dataset)
    
    # Get training data
    data = get_training_data(dataset)
    
    # Create splits
    train_data, val_data, test_data = create_train_val_test_split(data)
    
    # Format for T5
    train_formatted = format_for_t5(train_data)
    val_formatted = format_for_t5(val_data)
    test_formatted = format_for_t5(test_data)
    
    return {
        'train': train_formatted,
        'validation': val_formatted,
        'test': test_formatted,
        'metadata': dataset['metadata']
    }

if __name__ == "__main__":
    # Example usage
    print("🚀 Loading Clinical NLQ Training Dataset...")
    
    # Load the dataset
    dataset = load_clinical_nlq_dataset()
    
    # Print statistics
    print_dataset_stats(dataset)
    
    # Get the data
    data = get_training_data(dataset)
    
    # Create train/val/test splits
    train_data, val_data, test_data = create_train_val_test_split(data)
    
    # Format for T5 training
    train_formatted = format_for_t5(train_data)
    val_formatted = format_for_t5(val_data)
    test_formatted = format_for_t5(test_data)
    
    # Save splits
    save_splits_to_json(train_formatted, val_formatted, test_formatted)
    
    print("\n✅ Dataset loaded and prepared successfully!")
    print("🎯 Ready for T5 model training in Colab!")
    
    # Show a few examples
    print(f"\n📝 Sample Training Examples:")
    for i, example in enumerate(train_formatted[:3]):
        print(f"\nExample {i+1}:")
        print(f"  Input: {example['input_text'][:100]}...")
        print(f"  Target: {example['target_text'][:100]}...")
        print(f"  Category: {example['category']}")