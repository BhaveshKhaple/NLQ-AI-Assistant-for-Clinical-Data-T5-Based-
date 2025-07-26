#!/usr/bin/env python
# coding: utf-8

# # Clinical NLQ to SQL: T5 Model Training
# 
# This notebook implements the training pipeline for a T5 model that converts natural language questions (NLQ) about clinical data to SQL queries. The model is trained on the Synthea dataset schema.
# 
# ## Overview
# 
# 1. **Environment Setup**: Install dependencies and configure the environment
# 2. **Data Generation**: Create training data of NLQ-SQL pairs
# 3. **Data Preprocessing**: Prepare the data for T5 model training
# 4. **Model Training**: Fine-tune a T5 model on the prepared data
# 5. **Model Evaluation**: Evaluate the model's performance
# 6. **Model Saving**: Save the trained model for later use
# 
# Let's get started!

# ## 1. Environment Setup
# 
# First, let's install the necessary libraries and set up our environment.

# Install required packages
# pip install transformers datasets torch pandas scikit-learn sqlparse nltk

# Import necessary libraries
import os
import re
import json
import pandas as pd
import numpy as np
import torch
import nltk
import sqlparse
from sklearn.model_selection import train_test_split
from datasets import Dataset, DatasetDict
from transformers import (
    T5ForConditionalGeneration,
    T5Tokenizer,
    Trainer,
    TrainingArguments,
    DataCollatorForSeq2Seq,
    EvalPrediction
)
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from tqdm.auto import tqdm

# Download NLTK resources
nltk.download('punkt')

# Mount Google Drive for saving model and data
from google.colab import drive
drive.mount('/content/drive')

# Create directories for saving model and data
BASE_DIR = '/content/drive/MyDrive/clinical_nlq_to_sql'
MODEL_DIR = f'{BASE_DIR}/models/fine_tuned_t5_synthea'
DATA_DIR = f'{BASE_DIR}/data'

# Create directories if they don't exist
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

print(f"Model will be saved to: {MODEL_DIR}")
print(f"Data will be saved to: {DATA_DIR}")

# Check for GPU availability
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

if device.type == "cuda":
    print(f"GPU Name: {torch.cuda.get_device_name(0)}")
    print(f"Available GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
else:
    print("WARNING: No GPU detected. Training will be slow on CPU.")

# ## 2. Data Generation & Loading
# 
# In this section, we'll generate or load diverse clinical questions and their corresponding SQL queries for the Synthea database schema.

# Define the Synthea database schema
SCHEMA_INFO = """
-- Clinical NLQ AI Assistant Database Schema
-- PostgreSQL 17+ Compatible Schema for Synthea Clinical Data

-- Core Patient Tables
CREATE TABLE clinical_data.patients (
    id UUID PRIMARY KEY,
    birth_date DATE NOT NULL,
    death_date DATE,
    ssn VARCHAR(11),
    drivers VARCHAR(20),
    passport VARCHAR(20),
    prefix VARCHAR(10),
    first_name VARCHAR(50),
    middle_name VARCHAR(50),
    last_name VARCHAR(50),
    suffix VARCHAR(10),
    maiden_name VARCHAR(50),
    marital_status VARCHAR(1),
    race VARCHAR(50),
    ethnicity VARCHAR(50),
    gender VARCHAR(1) NOT NULL,
    birth_place VARCHAR(200),
    address VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(50),
    county VARCHAR(100),
    fips VARCHAR(10),
    zip VARCHAR(10),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    healthcare_expenses DECIMAL(12, 2),
    healthcare_coverage DECIMAL(12, 2),
    income DECIMAL(12, 2)
);

CREATE TABLE clinical_data.organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    address VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(10),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    phone VARCHAR(20),
    revenue DECIMAL(15, 2),
    utilization INTEGER
);

CREATE TABLE clinical_data.providers (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES clinical_data.organizations(id),
    name VARCHAR(200) NOT NULL,
    gender VARCHAR(1),
    speciality VARCHAR(100),
    address VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(10),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    utilization INTEGER
);

CREATE TABLE clinical_data.encounters (
    id UUID PRIMARY KEY,
    start_time TIMESTAMP NOT NULL,
    stop_time TIMESTAMP,
    patient_id UUID NOT NULL REFERENCES clinical_data.patients(id),
    organization_id UUID REFERENCES clinical_data.organizations(id),
    provider_id UUID REFERENCES clinical_data.providers(id),
    encounter_class VARCHAR(50),
    code VARCHAR(20),
    description TEXT,
    base_encounter_cost DECIMAL(10, 2),
    total_claim_cost DECIMAL(10, 2),
    reason_code VARCHAR(20),
    reason_description TEXT
);

CREATE TABLE clinical_data.conditions (
    id UUID PRIMARY KEY,
    start_date DATE NOT NULL,
    stop_date DATE,
    patient_id UUID NOT NULL REFERENCES clinical_data.patients(id),
    encounter_id UUID REFERENCES clinical_data.encounters(id),
    system VARCHAR(50) NOT NULL,
    code VARCHAR(20) NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE clinical_data.medications (
    id UUID PRIMARY KEY,
    start_date DATE NOT NULL,
    stop_date DATE,
    patient_id UUID NOT NULL REFERENCES clinical_data.patients(id),
    encounter_id UUID REFERENCES clinical_data.encounters(id),
    code VARCHAR(20),
    description TEXT NOT NULL,
    base_cost DECIMAL(10, 2),
    dispenses INTEGER,
    total_cost DECIMAL(10, 2),
    reason_code VARCHAR(20),
    reason_description TEXT
);

CREATE TABLE clinical_data.observations (
    id UUID PRIMARY KEY,
    date DATE NOT NULL,
    patient_id UUID NOT NULL REFERENCES clinical_data.patients(id),
    encounter_id UUID REFERENCES clinical_data.encounters(id),
    category VARCHAR(100),
    code VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    value VARCHAR(200),
    units VARCHAR(50),
    type VARCHAR(50)
);
"""

# Save schema to a file
with open(f"{DATA_DIR}/synthea_schema.sql", "w") as f:
    f.write(SCHEMA_INFO)

print(f"Schema saved to {DATA_DIR}/synthea_schema.sql")

# Define sample NLQ-SQL pairs based on the tester file
SAMPLE_QUERIES = [
    {
        "nlq": "How many patients do we have?",
        "sql": "SELECT COUNT(*) as patient_count FROM clinical_data.patients",
        "category": "basic_count"
    },
    {
        "nlq": "Show me all female patients",
        "sql": "SELECT first_name, last_name, birth_date FROM clinical_data.patients WHERE gender = 'F'",
        "category": "basic_filter"
    },
    {
        "nlq": "What are the most common conditions?",
        "sql": "SELECT description, COUNT(*) as frequency FROM clinical_data.conditions GROUP BY description ORDER BY frequency DESC LIMIT 10",
        "category": "aggregation"
    },
    {
        "nlq": "Show patients with diabetes",
        "sql": "SELECT DISTINCT p.first_name, p.last_name, p.birth_date FROM clinical_data.patients p JOIN clinical_data.conditions c ON p.id = c.patient_id WHERE c.description ILIKE '%diabetes%'",
        "category": "join_filter"
    },
    {
        "nlq": "How many encounters did each patient have?",
        "sql": "SELECT p.first_name, p.last_name, COUNT(e.id) as encounter_count FROM clinical_data.patients p LEFT JOIN clinical_data.encounters e ON p.id = e.patient_id GROUP BY p.id, p.first_name, p.last_name ORDER BY encounter_count DESC",
        "category": "join_aggregation"
    },
    {
        "nlq": "What medications are prescribed for hypertension?",
        "sql": "SELECT DISTINCT m.description as medication, COUNT(*) as prescription_count FROM clinical_data.medications m WHERE m.reason_description ILIKE '%hypertension%' GROUP BY m.description ORDER BY prescription_count DESC",
        "category": "medication_analysis"
    },
    {
        "nlq": "Show patient demographics by age group",
        "sql": "SELECT CASE WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, birth_date)) < 18 THEN 'Under 18' WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, birth_date)) BETWEEN 18 AND 30 THEN '18-30' WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, birth_date)) BETWEEN 31 AND 50 THEN '31-50' WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, birth_date)) BETWEEN 51 AND 70 THEN '51-70' ELSE 'Over 70' END as age_group, gender, COUNT(*) as patient_count FROM clinical_data.patients GROUP BY age_group, gender ORDER BY age_group, gender",
        "category": "complex_aggregation"
    },
    {
        "nlq": "Find patients with multiple chronic conditions",
        "sql": "SELECT p.first_name, p.last_name, COUNT(DISTINCT c.description) as condition_count, STRING_AGG(DISTINCT c.description, '; ') as conditions FROM clinical_data.patients p JOIN clinical_data.conditions c ON p.id = c.patient_id WHERE c.description ILIKE ANY(ARRAY['%diabetes%', '%hypertension%', '%heart%', '%kidney%']) GROUP BY p.id, p.first_name, p.last_name HAVING COUNT(DISTINCT c.description) >= 2 ORDER BY condition_count DESC",
        "category": "complex_clinical"
    }
]

# Function to generate more diverse NLQ-SQL pairs
def generate_more_queries():
    """Generate additional NLQ-SQL pairs based on patterns"""
    additional_queries = [
        # Basic counts and filters
        {
            "nlq": "Count the number of male patients",
            "sql": "SELECT COUNT(*) as male_patient_count FROM clinical_data.patients WHERE gender = 'M'",
            "category": "basic_filter"
        },
        {
            "nlq": "How many patients are from California?",
            "sql": "SELECT COUNT(*) as ca_patient_count FROM clinical_data.patients WHERE state = 'CA'",
            "category": "basic_filter"
        },
        {
            "nlq": "List all patients older than 65",
            "sql": "SELECT first_name, last_name, birth_date FROM clinical_data.patients WHERE EXTRACT(YEAR FROM AGE(CURRENT_DATE, birth_date)) > 65",
            "category": "basic_filter"
        },
        
        # Aggregations
        {
            "nlq": "What is the average age of our patients?",
            "sql": "SELECT AVG(EXTRACT(YEAR FROM AGE(CURRENT_DATE, birth_date))) as average_age FROM clinical_data.patients",
            "category": "aggregation"
        },
        {
            "nlq": "What are the top 5 medications prescribed?",
            "sql": "SELECT description, COUNT(*) as prescription_count FROM clinical_data.medications GROUP BY description ORDER BY prescription_count DESC LIMIT 5",
            "category": "aggregation"
        },
        
        # Joins
        {
            "nlq": "Show all conditions for patient with ID '123e4567-e89b-12d3-a456-426614174000'",
            "sql": "SELECT c.description, c.start_date, c.stop_date FROM clinical_data.conditions c WHERE c.patient_id = '123e4567-e89b-12d3-a456-426614174000' ORDER BY c.start_date DESC",
            "category": "join_filter"
        },
        {
            "nlq": "List all medications prescribed to patients with heart disease",
            "sql": "SELECT DISTINCT m.description, COUNT(*) as count FROM clinical_data.medications m JOIN clinical_data.patients p ON m.patient_id = p.id JOIN clinical_data.conditions c ON p.id = c.patient_id WHERE c.description ILIKE '%heart disease%' GROUP BY m.description ORDER BY count DESC",
            "category": "join_filter"
        },
        
        # Complex queries
        {
            "nlq": "Find patients who had both diabetes and hypertension",
            "sql": "SELECT p.first_name, p.last_name FROM clinical_data.patients p WHERE p.id IN (SELECT patient_id FROM clinical_data.conditions WHERE description ILIKE '%diabetes%') AND p.id IN (SELECT patient_id FROM clinical_data.conditions WHERE description ILIKE '%hypertension%')",
            "category": "complex_clinical"
        },
        {
            "nlq": "Which providers have the highest number of patient encounters?",
            "sql": "SELECT pr.name as provider_name, pr.speciality, COUNT(e.id) as encounter_count FROM clinical_data.providers pr JOIN clinical_data.encounters e ON pr.id = e.provider_id GROUP BY pr.id, pr.name, pr.speciality ORDER BY encounter_count DESC LIMIT 10",
            "category": "join_aggregation"
        },
        
        # Temporal queries
        {
            "nlq": "Show encounters from the last 30 days",
            "sql": "SELECT e.id, e.start_time, p.first_name, p.last_name, e.description FROM clinical_data.encounters e JOIN clinical_data.patients p ON e.patient_id = p.id WHERE e.start_time >= CURRENT_DATE - INTERVAL '30 days' ORDER BY e.start_time DESC",
            "category": "temporal_analysis"
        },
        {
            "nlq": "What is the average duration of hospital stays?",
            "sql": "SELECT AVG(EXTRACT(EPOCH FROM (stop_time - start_time))/3600) as avg_duration_hours FROM clinical_data.encounters WHERE stop_time IS NOT NULL AND encounter_class = 'inpatient'",
            "category": "temporal_analysis"
        }
    ]
    return additional_queries

# Generate additional queries
additional_queries = generate_more_queries()
all_queries = SAMPLE_QUERIES + additional_queries

print(f"Total number of query pairs: {len(all_queries)}")

# Save queries to a file
with open(f"{DATA_DIR}/nlq_sql_pairs.json", "w") as f:
    json.dump(all_queries, f, indent=2)

print(f"Query pairs saved to {DATA_DIR}/nlq_sql_pairs.json")

# Function to generate more training examples through variations
def generate_variations(queries, num_variations=3):
    """Generate variations of existing queries to expand the dataset"""
    variations = []
    
    # Simple variations for demonstration
    variations_templates = {
        "How many": ["Count the number of", "What is the total number of", "How many total"],
        "Show me": ["Display", "List", "I want to see", "Can you show"],
        "What are": ["Tell me about", "I need to know", "Could you list", "What's"],
        "Find": ["Identify", "Search for", "Look for", "Locate"]
    }
    
    for query in queries:
        nlq = query["nlq"]
        sql = query["sql"]
        category = query["category"]
        
        # Add the original query
        variations.append(query)
        
        # Generate variations
        for template, replacements in variations_templates.items():
            if nlq.startswith(template):
                for replacement in replacements:
                    new_nlq = nlq.replace(template, replacement, 1)
                    variations.append({
                        "nlq": new_nlq,
                        "sql": sql,
                        "category": category
                    })
    
    return variations

# Generate variations
expanded_queries = generate_variations(all_queries)
print(f"Expanded to {len(expanded_queries)} query pairs with variations")

# Save expanded queries
with open(f"{DATA_DIR}/nlq_sql_pairs_expanded.json", "w") as f:
    json.dump(expanded_queries, f, indent=2)

print(f"Expanded query pairs saved to {DATA_DIR}/nlq_sql_pairs_expanded.json")

# ## 3. Data Preprocessing for T5
# 
# Now we'll preprocess the data for the T5 model, including tokenization and formatting.

# Load the expanded query pairs
with open(f"{DATA_DIR}/nlq_sql_pairs_expanded.json", "r") as f:
    expanded_queries = json.load(f)

# Create a pandas DataFrame
df = pd.DataFrame(expanded_queries)
print(f"Dataset shape: {df.shape}")
print(df.head())

# Format the input and target for T5
def format_for_t5(row, schema_info):
    """Format the input and target for T5 model"""
    # Input: question + schema context
    input_text = f"question: {row['nlq']} context: {schema_info}"
    
    # Target: SQL query
    target_text = row['sql']
    
    return {
        "input": input_text,
        "target": target_text,
        "category": row['category']
    }

# Apply formatting
formatted_data = [format_for_t5(row, SCHEMA_INFO) for _, row in df.iterrows()]
formatted_df = pd.DataFrame(formatted_data)
print(f"Formatted dataset shape: {formatted_df.shape}")
print(formatted_df.head())

# Split the data into train, validation, and test sets
train_df, temp_df = train_test_split(formatted_df, test_size=0.3, random_state=42)
val_df, test_df = train_test_split(temp_df, test_size=0.5, random_state=42)

print(f"Train set: {train_df.shape[0]} examples")
print(f"Validation set: {val_df.shape[0]} examples")
print(f"Test set: {test_df.shape[0]} examples")

# Convert to Hugging Face datasets
train_dataset = Dataset.from_pandas(train_df)
val_dataset = Dataset.from_pandas(val_df)
test_dataset = Dataset.from_pandas(test_df)

# Combine into a DatasetDict
dataset = DatasetDict({
    'train': train_dataset,
    'validation': val_dataset,
    'test': test_dataset
})

print(dataset)

# Initialize the T5 tokenizer
tokenizer = T5Tokenizer.from_pretrained("t5-small")

# Set maximum input and output lengths
MAX_INPUT_LENGTH = 512
MAX_TARGET_LENGTH = 128

# Tokenization function
def preprocess_function(examples):
    """Tokenize the inputs and targets"""
    inputs = examples["input"]
    targets = examples["target"]
    
    # Tokenize inputs
    model_inputs = tokenizer(
        inputs, 
        max_length=MAX_INPUT_LENGTH,
        padding="max_length",
        truncation=True,
        return_tensors="pt"
    )
    
    # Tokenize targets
    labels = tokenizer(
        targets,
        max_length=MAX_TARGET_LENGTH,
        padding="max_length",
        truncation=True,
        return_tensors="pt"
    )
    
    # Replace padding token id with -100 so it's ignored in loss calculation
    labels = labels["input_ids"]
    labels[labels == tokenizer.pad_token_id] = -100
    
    model_inputs["labels"] = labels
    
    return model_inputs

# Apply preprocessing to all splits
tokenized_datasets = dataset.map(
    preprocess_function,
    batched=True,
    remove_columns=["input", "target", "category", "__index_level_0__"]
)

print(tokenized_datasets)

# ## 4. Model Configuration & Fine-tuning
# 
# Now we'll configure and fine-tune the T5 model on our preprocessed data.

# Load the pre-trained T5 model
model = T5ForConditionalGeneration.from_pretrained("t5-small").to(device)
print(f"Model loaded: t5-small")

# Define training arguments
training_args = TrainingArguments(
    output_dir=MODEL_DIR,
    evaluation_strategy="epoch",
    learning_rate=5e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    weight_decay=0.01,
    save_total_limit=3,
    num_train_epochs=5,
    predict_with_generate=True,
    logging_dir=f"{MODEL_DIR}/logs",
    logging_steps=100,
    save_strategy="epoch"
)

# Define data collator
data_collator = DataCollatorForSeq2Seq(
    tokenizer=tokenizer,
    model=model,
    padding=True
)

# Define metrics for evaluation
def compute_metrics(eval_preds):
    """Compute BLEU score and exact match accuracy"""
    preds, labels = eval_preds
    
    # Decode predictions and labels
    decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
    
    # Replace -100 with pad token id
    labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
    decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
    
    # Compute BLEU score
    bleu_scores = []
    smoothie = SmoothingFunction().method1
    
    for pred, label in zip(decoded_preds, decoded_labels):
        pred_tokens = pred.split()
        label_tokens = label.split()
        bleu_score = sentence_bleu([label_tokens], pred_tokens, smoothing_function=smoothie)
        bleu_scores.append(bleu_score)
    
    # Compute exact match accuracy
    exact_matches = sum(1 for pred, label in zip(decoded_preds, decoded_labels) if pred.strip() == label.strip())
    exact_match_accuracy = exact_matches / len(decoded_preds)
    
    return {
        "bleu": np.mean(bleu_scores),
        "exact_match": exact_match_accuracy
    }

# Initialize the Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["validation"],
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics
)

# Train the model
print("Starting model training...")
trainer.train()
print("Training complete!")

# ## 5. Model Evaluation
# 
# Let's evaluate the fine-tuned model on the test set.

# Evaluate on the test set
test_results = trainer.evaluate(tokenized_datasets["test"])
print(f"Test results: {test_results}")

# Function to generate SQL from natural language
def generate_sql(question, schema_info=SCHEMA_INFO):
    """Generate SQL query from natural language question"""
    # Format input
    input_text = f"question: {question} context: {schema_info}"
    input_ids = tokenizer(input_text, return_tensors="pt").input_ids.to(device)
    
    # Generate output
    outputs = model.generate(
        input_ids,
        max_length=MAX_TARGET_LENGTH,
        num_beams=5,
        early_stopping=True
    )
    
    # Decode output
    generated_sql = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Format SQL
    formatted_sql = sqlparse.format(generated_sql, reindent=True, keyword_case='upper')
    
    return formatted_sql

# Test with some examples
test_questions = [
    "How many patients do we have?",
    "Show me all female patients",
    "What are the most common conditions?",
    "Find patients with diabetes"
]

for question in test_questions:
    sql = generate_sql(question)
    print(f"Question: {question}")
    print(f"Generated SQL: {sql}")
    print("-" * 50)

# ## 6. Model Saving
# 
# Finally, let's save the fine-tuned model for later use.

# Save the model and tokenizer
model_save_path = f"{MODEL_DIR}/final_model"
model.save_pretrained(model_save_path)
tokenizer.save_pretrained(model_save_path)

print(f"Model and tokenizer saved to {model_save_path}")

# Save model configuration and metadata
model_metadata = {
    "model_name": "t5-small-synthea-nlq-to-sql",
    "base_model": "t5-small",
    "training_date": pd.Timestamp.now().strftime("%Y-%m-%d"),
    "dataset_size": len(expanded_queries),
    "train_size": len(train_df),
    "val_size": len(val_df),
    "test_size": len(test_df),
    "test_metrics": test_results,
    "max_input_length": MAX_INPUT_LENGTH,
    "max_target_length": MAX_TARGET_LENGTH,
    "training_args": training_args.to_dict()
}

with open(f"{model_save_path}/model_metadata.json", "w") as f:
    json.dump(model_metadata, f, indent=2, default=str)

print(f"Model metadata saved to {model_save_path}/model_metadata.json")

# ## Conclusion
# 
# In this notebook, we've successfully:
# 
# 1. Set up the environment with all necessary dependencies
# 2. Generated diverse NLQ-SQL pairs for the Synthea database schema
# 3. Preprocessed the data for T5 model training
# 4. Fine-tuned a T5 model on our dataset
# 5. Evaluated the model's performance
# 6. Saved the model for later use
# 
# The trained model can now be used to convert natural language questions about clinical data to SQL queries, enabling non-technical users to query the Synthea database without knowing SQL.