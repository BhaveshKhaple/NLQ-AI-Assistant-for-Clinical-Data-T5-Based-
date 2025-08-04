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
from transformers import T5ForConditionalGeneration, T5Tokenizer, AutoTokenizer
import yaml
from .fallback_sql_generator import FallbackSQLGenerator
from .query_preprocessor import QueryPreprocessor
from .intelligent_fallback import IntelligentFallback

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
        
        # Initialize fallback generators and preprocessor
        self.fallback_generator = FallbackSQLGenerator()
        self.query_preprocessor = QueryPreprocessor()
        self.intelligent_fallback = IntelligentFallback()
        
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
        Build schema context string to match the training data format.
        This will be appended to queries for better SQL generation.
        """
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
        return schema_context.strip()
    
    def _clean_generated_sql(self, sql: str) -> str:
        """
        Clean up common tokenization artifacts in generated SQL.
        
        Args:
            sql: Raw generated SQL
            
        Returns:
            Cleaned SQL
        """
        import re
        
        # Remove extra spaces around common SQL keywords and operators
        sql = re.sub(r'\s+', ' ', sql)  # Replace multiple spaces with single space
        sql = re.sub(r'\s*,\s*', ', ', sql)  # Fix comma spacing
        sql = re.sub(r'\s*\(\s*', '(', sql)  # Fix opening parentheses
        sql = re.sub(r'\s*\)\s*', ')', sql)  # Fix closing parentheses
        sql = re.sub(r'\s*=\s*', ' = ', sql)  # Fix equals spacing
        sql = re.sub(r'\s*<\s*', ' < ', sql)  # Fix less than spacing
        sql = re.sub(r'\s*>\s*', ' > ', sql)  # Fix greater than spacing
        sql = re.sub(r'\s*<=\s*', ' <= ', sql)  # Fix less than or equal spacing
        sql = re.sub(r'\s*>=\s*', ' >= ', sql)  # Fix greater than or equal spacing
        sql = re.sub(r'\s*<>\s*', ' <> ', sql)  # Fix not equal spacing
        sql = re.sub(r'\s*!=\s*', ' != ', sql)  # Fix not equal spacing
        
        # Fix common column name issues with underscores
        sql = re.sub(r'start_\s+date', 'start_date', sql)  # Fix "start_ date" -> "start_date"
        sql = re.sub(r'stop_\s+date', 'stop_date', sql)  # Fix "stop_ date" -> "stop_date"
        sql = re.sub(r'end_\s+date', 'end_date', sql)  # Fix "end_ date" -> "end_date"
        sql = re.sub(r'first_\s+name', 'first_name', sql)  # Fix "first_ name" -> "first_name"
        sql = re.sub(r'last_\s+name', 'last_name', sql)  # Fix "last_ name" -> "last_name"
        sql = re.sub(r'patient_\s+id', 'patient_id', sql)  # Fix "patient_ id" -> "patient_id"
        sql = re.sub(r'encounter_\s+id', 'encounter_id', sql)  # Fix "encounter_ id" -> "encounter_id"
        sql = re.sub(r'provider_\s+id', 'provider_id', sql)  # Fix "provider_ id" -> "provider_id"
        
        # Fix ORDER BY clause spacing issues
        sql = re.sub(r'ORDER\s+BY\s+(\w+)_\s+(\w+)', r'ORDER BY \1_\2', sql)
        
        # Fix common SQL keyword spacing
        sql = re.sub(r'\s+FROM\s+', ' FROM ', sql)
        sql = re.sub(r'\s+WHERE\s+', ' WHERE ', sql)
        sql = re.sub(r'\s+ORDER\s+BY\s+', ' ORDER BY ', sql)
        sql = re.sub(r'\s+GROUP\s+BY\s+', ' GROUP BY ', sql)
        sql = re.sub(r'\s+HAVING\s+', ' HAVING ', sql)
        sql = re.sub(r'\s+JOIN\s+', ' JOIN ', sql)
        sql = re.sub(r'\s+LEFT\s+JOIN\s+', ' LEFT JOIN ', sql)
        sql = re.sub(r'\s+RIGHT\s+JOIN\s+', ' RIGHT JOIN ', sql)
        sql = re.sub(r'\s+INNER\s+JOIN\s+', ' INNER JOIN ', sql)
        sql = re.sub(r'\s+ON\s+', ' ON ', sql)
        sql = re.sub(r'\s+AND\s+', ' AND ', sql)
        sql = re.sub(r'\s+OR\s+', ' OR ', sql)
        sql = re.sub(r'\s+LIMIT\s+', ' LIMIT ', sql)
        sql = re.sub(r'\s+OFFSET\s+', ' OFFSET ', sql)
        
        # Fix missing spaces after functions and keywords
        sql = re.sub(r'COUNT\(\*\)FROM', 'COUNT(*) FROM', sql)
        sql = re.sub(r'SELECT\s*COUNT\(\*\)FROM', 'SELECT COUNT(*) FROM', sql)
        sql = re.sub(r'(\w+)\(([^)]*)\)FROM', r'\1(\2) FROM', sql)  # General function spacing
        
        return sql.strip()
    
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
                    "d:/projects/healthca/models/trained/t5_clinical_model",  # Main model directory
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
            
            # Load tokenizer - use AutoTokenizer to automatically detect the correct tokenizer type
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
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
            # Step 1: Preprocess the query to match training patterns
            preprocessing_result = self.query_preprocessor.preprocess_query(nlq)
            
            # Use preprocessed query if mapping was applied with high confidence
            if preprocessing_result['mapping_applied'] and preprocessing_result['confidence'] > 0.8:
                processed_nlq = preprocessing_result['preprocessed_query']
                logger.info(f"🔄 Query preprocessed: '{nlq}' -> '{processed_nlq}'")
            else:
                processed_nlq = nlq
            
            # Use config defaults if parameters not provided
            max_length = max_length or self.config.get('model', {}).get('max_target_length', 512)
            num_beams = num_beams or 4
            temperature = temperature or 1.0
            do_sample = do_sample if do_sample is not None else False
            
            # Format input to match training data format
            if include_schema_context:
                input_text = f"translate to sql: {processed_nlq} {self.schema_context}"
            else:
                input_text = f"translate to sql: {processed_nlq}"
            
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
            
            # Post-process to fix common tokenization issues
            generated_sql = self._clean_generated_sql(generated_sql)
            
            generation_time = time.time() - start_time
            
            # Update statistics
            self.generation_stats['total_queries'] += 1
            self.generation_stats['total_time'] += generation_time
            self.generation_stats['avg_time'] = self.generation_stats['total_time'] / self.generation_stats['total_queries']
            
            # Validate generated SQL
            validation_result = self._validate_sql(generated_sql)
            
            # If T5 model generated invalid SQL, try intelligent fallback first
            if not validation_result['is_valid']:
                logger.warning(f"⚠️ T5 model generated invalid SQL, trying intelligent fallback...")
                fallback_result = self.intelligent_fallback.generate_sql(nlq)
                
                # If intelligent fallback also fails, try basic fallback
                if not fallback_result['validation']['is_valid']:
                    logger.warning(f"⚠️ Intelligent fallback failed, trying basic fallback...")
                    fallback_result = self.fallback_generator.generate_sql(nlq)
                
                if fallback_result['validation']['is_valid']:
                    logger.info(f"✅ Fallback generator produced valid SQL")
                    self.generation_stats['successful_generations'] += 1
                    
                    # Merge results
                    result = {
                        'nlq': nlq,
                        'generated_sql': fallback_result['generated_sql'],
                        'generation_time': generation_time,
                        'generation_config': generation_config,
                        'validation': fallback_result['validation'],
                        'metadata': {
                            'method': 'fallback_after_t5_failure',
                            'original_t5_sql': generated_sql,
                            'original_t5_errors': validation_result['errors'],
                            'fallback_method': fallback_result['method'],
                            'fallback_confidence': fallback_result['confidence'],
                            'input_length': len(input_text),
                            'schema_context_used': include_schema_context,
                            'preprocessing': preprocessing_result
                        }
                    }
                    
                    logger.info(f"✅ Fallback SQL generated: {fallback_result['generated_sql'][:100]}...")
                    return result
                else:
                    self.generation_stats['failed_generations'] += 1
            else:
                self.generation_stats['successful_generations'] += 1
            
            result = {
                'nlq': nlq,
                'generated_sql': generated_sql,
                'generation_time': generation_time,
                'generation_config': generation_config,
                'validation': validation_result,
                'metadata': {
                    'method': 't5_model',
                    'input_length': len(input_text),
                    'output_length': len(generated_sql),
                    'tokens_generated': len(outputs[0]),
                    'schema_context_used': include_schema_context,
                    'preprocessing': preprocessing_result
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
        
        # Check for valid table names
        valid_tables = [
            'clinical_data.patients', 'clinical_data.conditions', 'clinical_data.medications',
            'clinical_data.encounters', 'clinical_data.providers', 'clinical_data.organizations',
            'clinical_data.immunizations', 'clinical_data.procedures', 'clinical_data.observations',
            'clinical_data.allergies', 'clinical_data.claims', 'clinical_data.payers',
            'clinical_data.care_plans', 'clinical_data.careplans', 'clinical_data.devices',
            'clinical_data.supplies', 'clinical_data.imaging_studies', 'clinical_data.payer_transitions',
            'clinical_data.claims_transactions'
        ]
        
        # Extract table references from SQL
        import re
        table_pattern = r'clinical_data\.\w+'
        found_tables = re.findall(table_pattern, sql)
        
        for table in found_tables:
            if table not in valid_tables:
                errors.append(f"Invalid table reference: '{table}'")
        
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