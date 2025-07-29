#!/usr/bin/env python3
"""
Clinical Inference Engine
Handles T5 model loading, tokenization, and SQL generation from natural language queries.
"""

import os
import torch
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from transformers import T5ForConditionalGeneration, T5Tokenizer
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClinicalInferenceEngine:
    """
    T5-based inference engine for converting natural language queries to SQL.
    Supports multiple model versions and generation strategies.
    """
    
    def __init__(self, config_path: str = "d:/projects/healthca/config/config.yaml"):
        """
        Initialize the inference engine.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.model = None
        self.tokenizer = None
        self.device = None
        self.model_info = {}
        self.generation_stats = {
            'total_queries': 0,
            'total_time': 0.0,
            'avg_time': 0.0,
            'successful_generations': 0,
            'failed_generations': 0
        }
        
        # Schema context for better SQL generation
        self.schema_context = self._build_schema_context()
        
        logger.info("🔧 Clinical Inference Engine initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"✅ Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            # Return default config
            return {
                'model': {
                    'max_source_length': 512,
                    'max_target_length': 512,
                    'device': 'auto',
                    'confidence_threshold': 0.7
                }
            }
    
    def _build_schema_context(self) -> str:
        """
        Build schema context string to help model understand database structure.
        This will be prepended to queries for better SQL generation.
        """
        schema_context = """
Database Schema Context:
- clinical_data.patients: Patient demographics and basic info
- clinical_data.conditions: Medical conditions and diagnoses  
- clinical_data.medications: Prescribed medications
- clinical_data.encounters: Healthcare visits and appointments
- clinical_data.providers: Healthcare providers and practitioners
- clinical_data.organizations: Healthcare organizations and facilities
- clinical_data.payers: Insurance and payment information

Always use 'clinical_data.' schema prefix in SQL queries.
"""
        return schema_context.strip()
    
    def load_model(self, model_path: Optional[str] = None) -> bool:
        """
        Load the trained T5 model and tokenizer.
        
        Args:
            model_path: Path to model directory. If None, uses config or default paths.
            
        Returns:
            bool: True if model loaded successfully, False otherwise
        """
        try:
            # Determine model path
            if model_path is None:
                # Try multiple possible paths based on the report
                possible_paths = [
                    "d:/projects/healthca/models/trained/t5_clinical_model/final_model",
                    "d:/projects/healthca/models/trained/t5_clinical_model/final model 2nd run",
                    "d:/projects/healthca/models/trained/t5_clinical_model/final model last",
                    self.config.get('model', {}).get('model_path', './models/clinical_t5')
                ]
                
                model_path = None
                for path in possible_paths:
                    if os.path.exists(path) and os.path.exists(os.path.join(path, 'config.json')):
                        model_path = path
                        break
                
                if model_path is None:
                    raise FileNotFoundError("No valid model found in expected locations")
            
            logger.info(f"📥 Loading model from: {model_path}")
            
            # Set device
            if self.config.get('model', {}).get('device') == 'auto':
                self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            else:
                self.device = torch.device(self.config.get('model', {}).get('device', 'cpu'))
            
            logger.info(f"🔧 Using device: {self.device}")
            
            # Load tokenizer
            self.tokenizer = T5Tokenizer.from_pretrained(model_path)
            logger.info("✅ Tokenizer loaded successfully")
            
            # Load model
            self.model = T5ForConditionalGeneration.from_pretrained(model_path)
            self.model.to(self.device)
            self.model.eval()
            logger.info("✅ Model loaded successfully")
            
            # Collect model information
            total_params = sum(p.numel() for p in self.model.parameters())
            trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
            model_size_mb = total_params * 4 / 1024 / 1024
            
            self.model_info = {
                'model_path': model_path,
                'total_parameters': total_params,
                'trainable_parameters': trainable_params,
                'model_size_mb': model_size_mb,
                'device': str(self.device)
            }
            
            logger.info(f"📊 Model Info:")
            logger.info(f"  Total parameters: {total_params:,}")
            logger.info(f"  Trainable parameters: {trainable_params:,}")
            logger.info(f"  Model size: ~{model_size_mb:.1f} MB")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
            return False
    
    def generate_sql(self, 
                    nlq: str, 
                    max_length: int = None,
                    num_beams: int = None,
                    temperature: float = None,
                    do_sample: bool = None,
                    no_repeat_ngram_size: int = 3,
                    early_stopping: bool = True,
                    include_schema_context: bool = True) -> Dict[str, Any]:
        """
        Generate SQL query from natural language question.
        
        Args:
            nlq: Natural language query
            max_length: Maximum length of generated SQL
            num_beams: Number of beams for beam search
            temperature: Sampling temperature
            do_sample: Whether to use sampling
            no_repeat_ngram_size: Prevent repetition of n-grams
            early_stopping: Whether to stop early
            include_schema_context: Whether to include schema context
            
        Returns:
            Dict containing generated SQL and metadata
        """
        if not self.model or not self.tokenizer:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        start_time = time.time()
        
        try:
            # Use config defaults if parameters not provided
            max_length = max_length or self.config.get('model', {}).get('max_target_length', 512)
            num_beams = num_beams or 4
            temperature = temperature or 1.0
            do_sample = do_sample if do_sample is not None else False
            
            # Format input with schema context if requested
            if include_schema_context:
                input_text = f"{self.schema_context}\n\ntranslate to sql: {nlq}"
            else:
                input_text = f"translate to sql: {nlq}"
            
            # Tokenize input
            inputs = self.tokenizer(
                input_text,
                return_tensors="pt",
                max_length=self.config.get('model', {}).get('max_source_length', 512),
                truncation=True,
                padding=True
            ).to(self.device)
            
            # Generate SQL
            with torch.no_grad():
                generation_config = {
                    'max_length': max_length,
                    'min_length': 10,
                    'num_beams': num_beams,
                    'early_stopping': early_stopping,
                    'no_repeat_ngram_size': no_repeat_ngram_size,
                    'pad_token_id': self.tokenizer.pad_token_id,
                    'eos_token_id': self.tokenizer.eos_token_id,
                    'length_penalty': 1.0
                }
                
                if do_sample:
                    generation_config.update({
                        'do_sample': True,
                        'temperature': temperature,
                        'top_p': 0.9
                    })
                else:
                    generation_config['do_sample'] = False
                
                outputs = self.model.generate(**inputs, **generation_config)
            
            # Decode generated SQL
            generated_sql = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            generated_sql = generated_sql.strip()
            
            generation_time = time.time() - start_time
            
            # Update statistics
            self.generation_stats['total_queries'] += 1
            self.generation_stats['total_time'] += generation_time
            self.generation_stats['avg_time'] = self.generation_stats['total_time'] / self.generation_stats['total_queries']
            
            # Validate generated SQL
            validation_result = self._validate_sql(generated_sql)
            
            if validation_result['is_valid']:
                self.generation_stats['successful_generations'] += 1
            else:
                self.generation_stats['failed_generations'] += 1
            
            result = {
                'nlq': nlq,
                'generated_sql': generated_sql,
                'generation_time': generation_time,
                'generation_config': generation_config,
                'validation': validation_result,
                'metadata': {
                    'input_length': len(input_text),
                    'output_length': len(generated_sql),
                    'tokens_generated': len(outputs[0]),
                    'schema_context_used': include_schema_context
                }
            }
            
            logger.info(f"✅ SQL generated in {generation_time:.3f}s: {generated_sql[:100]}...")
            
            return result
            
        except Exception as e:
            generation_time = time.time() - start_time
            self.generation_stats['total_queries'] += 1
            self.generation_stats['failed_generations'] += 1
            
            logger.error(f"❌ Error generating SQL: {e}")
            
            return {
                'nlq': nlq,
                'generated_sql': '',
                'generation_time': generation_time,
                'error': str(e),
                'validation': {'is_valid': False, 'errors': [str(e)]},
                'metadata': {'error': True}
            }
    
    def _validate_sql(self, sql: str) -> Dict[str, Any]:
        """
        Validate generated SQL for basic correctness.
        
        Args:
            sql: Generated SQL query
            
        Returns:
            Dict with validation results
        """
        errors = []
        warnings = []
        
        # Basic syntax checks
        sql_upper = sql.upper().strip()
        
        # Must start with SELECT
        if not sql_upper.startswith('SELECT'):
            errors.append("Query must start with SELECT")
        
        # Must have FROM clause
        if 'FROM' not in sql_upper:
            errors.append("Query must contain FROM clause")
        
        # Check for schema prefix
        if 'clinical_data.' not in sql:
            warnings.append("Query should use 'clinical_data.' schema prefix")
        
        # Check balanced parentheses
        if sql.count('(') != sql.count(')'):
            errors.append("Unbalanced parentheses")
        
        # Check for common repetition issues (from the report)
        words = sql.split()
        if len(words) > 3:
            # Check for repetitive patterns
            for i in range(len(words) - 2):
                if words[i] == words[i+1] == words[i+2]:
                    errors.append(f"Repetitive pattern detected: '{words[i]}'")
                    break
        
        # Check for nonsensical content
        nonsensical_patterns = ['MAN MAN', 'THEN THEN', 'MANY MANY']
        for pattern in nonsensical_patterns:
            if pattern in sql.upper():
                errors.append(f"Nonsensical pattern detected: '{pattern}'")
        
        is_valid = len(errors) == 0
        
        return {
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'has_schema_prefix': 'clinical_data.' in sql,
            'has_select': sql_upper.startswith('SELECT'),
            'has_from': 'FROM' in sql_upper,
            'has_where': 'WHERE' in sql_upper,
            'has_join': 'JOIN' in sql_upper,
            'sql_length': len(sql),
            'word_count': len(words)
        }
    
    def batch_generate(self, nlq_list: List[str], **generation_kwargs) -> List[Dict[str, Any]]:
        """
        Generate SQL for multiple natural language queries.
        
        Args:
            nlq_list: List of natural language queries
            **generation_kwargs: Arguments passed to generate_sql
            
        Returns:
            List of generation results
        """
        logger.info(f"🔄 Processing batch of {len(nlq_list)} queries")
        
        results = []
        for i, nlq in enumerate(nlq_list):
            logger.info(f"  Processing query {i+1}/{len(nlq_list)}")
            result = self.generate_sql(nlq, **generation_kwargs)
            results.append(result)
        
        logger.info(f"✅ Batch processing completed")
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            **self.model_info,
            'generation_stats': self.generation_stats.copy()
        }
    
    def reset_stats(self):
        """Reset generation statistics."""
        self.generation_stats = {
            'total_queries': 0,
            'total_time': 0.0,
            'avg_time': 0.0,
            'successful_generations': 0,
            'failed_generations': 0
        }
        logger.info("📊 Generation statistics reset")
    
    def benchmark_generation_params(self, test_queries: List[str]) -> Dict[str, Any]:
        """
        Benchmark different generation parameters on test queries.
        
        Args:
            test_queries: List of test queries
            
        Returns:
            Benchmark results
        """
        logger.info("⚡ Benchmarking generation parameters")
        
        parameter_sets = [
            {"num_beams": 1, "do_sample": False, "name": "Greedy"},
            {"num_beams": 4, "do_sample": False, "name": "Beam Search (4)"},
            {"num_beams": 8, "do_sample": False, "name": "Beam Search (8)"},
            {"num_beams": 4, "do_sample": True, "temperature": 0.7, "name": "Sampling (T=0.7)"},
            {"num_beams": 4, "do_sample": True, "temperature": 0.9, "name": "Sampling (T=0.9)"},
        ]
        
        benchmark_results = {}
        
        for param_set in parameter_sets:
            name = param_set.pop('name')
            logger.info(f"  Testing {name}...")
            
            results = []
            total_time = 0
            valid_count = 0
            
            for query in test_queries:
                result = self.generate_sql(query, **param_set)
                results.append(result)
                total_time += result['generation_time']
                if result['validation']['is_valid']:
                    valid_count += 1
            
            benchmark_results[name] = {
                'avg_time': total_time / len(test_queries),
                'validity_rate': valid_count / len(test_queries),
                'results': results,
                'parameters': param_set
            }
        
        logger.info("✅ Benchmarking completed")
        return benchmark_results