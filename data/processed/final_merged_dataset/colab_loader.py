"""
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
    print(f"\nDataset Summary:")
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
        print(f"\nSample training example:")
        example = dataset['train'][0]
        print(f"Input: {example['input_text'][:100]}...")
        print(f"Target: {example['target_text'][:100]}...")
