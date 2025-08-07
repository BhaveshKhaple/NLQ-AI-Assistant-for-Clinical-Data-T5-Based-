# Clinical NLQ to SQL Training Dataset

## Overview
This dataset contains **999 diverse natural language questions (NLQ) paired with SQL queries** for training a T5 model to convert clinical questions into executable SQL queries for the Synthea clinical database.

## Files
- `clinical_nlq_training_data.json` - Main dataset with metadata and all examples
- `train_data.json` - Training split (70% - 699 examples)
- `val_data.json` - Validation split (15% - 150 examples)  
- `test_data.json` - Test split (15% - 150 examples)

## Dataset Structure

### Main Dataset Format
```json
{
  "metadata": {
    "name": "Clinical NLQ to SQL Training Dataset",
    "version": "1.0",
    "total_examples": 999,
    "database_schema": "clinical_data (PostgreSQL)",
    "categories": { ... },
    "distribution": { ... }
  },
  "data": [
    {
      "nlq": "How many patients do we have?",
      "sql": "SELECT COUNT(*) as patient_count FROM clinical_data.patients",
      "category": "basic_count"
    }
  ]
}
```

### Training Split Format
```json
[
  {
    "input_text": "translate to sql: How many patients do we have? Database Schema: clinical_data...",
    "target_text": "SELECT COUNT(*) as patient_count FROM clinical_data.patients",
    "category": "basic_count",
    "original_nlq": "How many patients do we have?"
  }
]
```

## Query Categories & Distribution

| Category | Count | Percentage | Description |
|----------|-------|------------|-------------|
| **Basic Queries (20%)** | | |
| basic_count | 104 | 10.4% | Simple COUNT queries |
| basic_filter | 78 | 7.8% | Basic WHERE clauses |
| basic_list | 26 | 2.6% | Simple SELECT statements |
| **Intermediate Queries (25%)** | | |
| aggregation | 150 | 15.0% | GROUP BY, SUM, AVG queries |
| join_filter | 75 | 7.5% | Single table joins with filters |
| **Advanced Queries (30%)** | | |
| complex_clinical | 111 | 11.1% | Multi-condition clinical queries |
| financial_analysis | 99 | 9.9% | Cost and billing analysis |
| provider_analysis | 37 | 3.7% | Provider performance queries |
| care_management | 37 | 3.7% | Care coordination queries |
| **Complex Analytical (15%)** | | |
| temporal_analysis | 51 | 5.1% | Time-based analysis |
| cost_distribution | 21 | 2.1% | Statistical cost analysis |
| provider_ranking | 21 | 2.1% | Provider ranking queries |
| risk_analysis | 21 | 2.1% | Patient risk scoring |
| medication_analysis | 21 | 2.1% | Medication pattern analysis |
| trend_analysis | 21 | 2.1% | Trend analysis with window functions |
| seasonal_analysis | 21 | 2.1% | Seasonal pattern analysis |
| financial_trend | 21 | 2.1% | Financial trend analysis |
| **Temporal Queries (10%)** | | |
| temporal_filter | 14 | 1.4% | Date-based filtering |
| temporal_pattern | 14 | 1.4% | Time pattern analysis |
| care_timeline | 14 | 1.4% | Care timeline queries |
| care_gaps | 14 | 1.4% | Care gap identification |
| age_analysis | 14 | 1.4% | Age-based analysis |
| adherence_analysis | 14 | 1.4% | Medication adherence |

## Database Schema
The queries target a PostgreSQL database with the `clinical_data` schema containing:

### Core Tables
- `patients` - Patient demographics and information
- `organizations` - Healthcare facilities  
- `providers` - Healthcare providers/doctors
- `encounters` - Medical visits and encounters
- `conditions` - Medical diagnoses and conditions
- `medications` - Prescribed medications
- `procedures` - Medical procedures performed
- `observations` - Lab results and vital signs
- `immunizations` - Vaccination records
- `allergies` - Patient allergies
- `care_plans` - Treatment plans
- `payers` - Insurance companies

### Key Relationships
- `patients.id` → `conditions.patient_id`, `medications.patient_id`, `encounters.patient_id`
- `encounters.id` → `conditions.encounter_id`, `medications.encounter_id`
- `providers.id` → `encounters.provider_id`
- `organizations.id` → `encounters.organization_id`

## Usage

### Loading in Python
```python
from src.models.data_loader import load_clinical_nlq_dataset, create_train_val_test_split

# Load the full dataset
dataset = load_clinical_nlq_dataset()

# Get training data
data = dataset['data']

# Create splits
train_data, val_data, test_data = create_train_val_test_split(data)
```

### Loading in Google Colab
```python
# Upload the JSON file to Colab or mount Google Drive
import json

# Load dataset
with open('clinical_nlq_training_data.json', 'r') as f:
    dataset = json.load(f)

# Access the training examples
training_examples = dataset['data']

# Example: Format for T5
formatted_examples = []
for item in training_examples:
    formatted_examples.append({
        'input_text': f"translate to sql: {item['nlq']}",
        'target_text': item['sql']
    })
```

### For Hugging Face Datasets
```python
from datasets import Dataset

# Load and format data
dataset = load_clinical_nlq_dataset()
train_data, val_data, test_data = create_train_val_test_split(dataset['data'])

# Convert to HF datasets
train_dataset = Dataset.from_list(train_data)
val_dataset = Dataset.from_list(val_data)
test_dataset = Dataset.from_list(test_data)
```

## Quality Assurance
- All SQL queries use valid PostgreSQL syntax
- Queries reference the correct `clinical_data` schema
- Natural language questions are diverse and realistic
- Categories are balanced according to specified distribution
- All queries are executable against the Synthea database schema

## Training Recommendations
- Use T5-small or T5-base as the base model
- Input format: `"translate to sql: {question}"`
- Target format: Raw SQL query
- Recommended batch size: 8-16
- Learning rate: 3e-4 to 5e-4
- Epochs: 3-5

## Next Steps
1. Load this dataset in Google Colab
2. Fine-tune T5 model using the training split
3. Evaluate on validation split during training
4. Final evaluation on test split
5. Save the trained model for inference

## Contact
Generated for the Clinical NLQ AI Assistant project - Phase 4: T5 Model Training