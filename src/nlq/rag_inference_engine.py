#!/usr/bin/env python3
"""
RAG-Enhanced Clinical Inference Engine
Combines the original T5 model with RAG-enhanced query processing for better performance.
"""

import os
import torch
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from transformers import T5ForConditionalGeneration, T5Tokenizer, AutoTokenizer
import yaml

from .rag_enhanced_nlq import RAGEnhancedNLQ
from .fallback_sql_generator import FallbackSQLGenerator
from .query_preprocessor import QueryPreprocessor
from .intelligent_fallback import IntelligentFallback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGEnhancedInferenceEngine:
    """
    Enhanced inference engine that uses RAG to improve query processing before T5 model inference.
    """
    
    def __init__(self, config_path: str = "d:/projects/healthca/config/config.yaml"):
        """
        Initialize the RAG-enhanced inference engine.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.model = None
        self.tokenizer = None
        self.device = None
        self.model_info = {}
        
        # Initialize RAG system with Gemini support
        gemini_api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        openai_api_key = os.getenv('OPENAI_API_KEY')
        preferred_llm = self.config.get('rag', {}).get('preferred_llm', 'gemini')
        
        self.rag_system = RAGEnhancedNLQ(
            gemini_api_key=gemini_api_key,
            openai_api_key=openai_api_key,
            preferred_llm=preferred_llm
        )
        self.rag_enabled = False
        
        # Initialize fallback systems
        self.fallback_generator = FallbackSQLGenerator()
        self.query_preprocessor = QueryPreprocessor()
        self.intelligent_fallback = IntelligentFallback()
        
        # Statistics
        self.generation_stats = {
            'total_queries': 0,
            'total_time': 0.0,
            'avg_time': 0.0,
            'successful_generations': 0,
            'failed_generations': 0,
            'rag_enhanced_queries': 0,
            'rag_improved_results': 0
        }
        
        logger.info("🔧 RAG-Enhanced Clinical Inference Engine initialized")
    
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
                },
                'rag': {
                    'enabled': True,
                    'similarity_threshold': 0.7,
                    'use_llm_formatting': False  # Set to True if you have OpenAI API key
                }
            }
    
    def initialize_rag_system(self) -> bool:
        """Initialize the RAG system with training data."""
        try:
            logger.info("🔄 Initializing RAG system...")
            if self.rag_system.load_training_data():
                self.rag_enabled = True
                logger.info("✅ RAG system initialized successfully")
                return True
            else:
                logger.warning("⚠️ RAG system initialization failed, continuing without RAG")
                return False
        except Exception as e:
            logger.error(f"❌ Error initializing RAG system: {e}")
            return False
    
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
                possible_paths = [
                    "d:/projects/healthca/models/trained/t5_clinical_model",
                    "d:/projects/healthca/models/trained/modetest1",
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
            logger.info(f"  Model size: ~{model_size_mb:.1f} MB")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
            return False
    
    def generate_sql(self, 
                    nlq: str, 
                    use_rag: bool = True,
                    max_length: int = None,
                    num_beams: int = None,
                    temperature: float = None,
                    do_sample: bool = None) -> Dict[str, Any]:
        """
        Generate SQL query from natural language question using RAG enhancement.
        
        Args:
            nlq: Natural language query
            use_rag: Whether to use RAG enhancement
            max_length: Maximum length of generated SQL
            num_beams: Number of beams for beam search
            temperature: Sampling temperature
            do_sample: Whether to use sampling
            
        Returns:
            Dict containing generated SQL and metadata
        """
        if not self.model or not self.tokenizer:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        start_time = time.time()
        
        try:
            # Step 1: RAG Enhancement (if enabled and available)
            enhanced_query_info = None
            processed_nlq = nlq
            
            if use_rag and self.rag_enabled:
                logger.info("🔍 Applying RAG enhancement...")
                enhanced_query_info = self.rag_system.enhance_query(nlq)
                
                if enhanced_query_info['rag_enhanced']:
                    processed_nlq = enhanced_query_info['enhanced_query']
                    self.generation_stats['rag_enhanced_queries'] += 1
                    logger.info(f"✅ RAG enhanced: '{nlq}' -> '{processed_nlq}'")
                else:
                    logger.info("ℹ️ No RAG enhancement applied")
            
            # Step 2: Traditional preprocessing (as backup)
            preprocessing_result = self.query_preprocessor.preprocess_query(processed_nlq)
            
            if preprocessing_result['mapping_applied'] and preprocessing_result['confidence'] > 0.8:
                processed_nlq = preprocessing_result['preprocessed_query']
                logger.info(f"🔄 Additional preprocessing applied: '{processed_nlq}'")
            
            # Step 3: Create formatted input for T5 model
            if enhanced_query_info and enhanced_query_info['rag_enhanced']:
                # Use RAG system's formatting
                input_text = self.rag_system.create_formatted_input(processed_nlq)
            else:
                # Use traditional formatting
                schema_context = self._build_schema_context()
                input_text = f"translate to sql: {processed_nlq} {schema_context}"
            
            # Use config defaults if parameters not provided
            max_length = max_length or self.config.get('model', {}).get('max_target_length', 512)
            num_beams = num_beams or 4
            temperature = temperature or 1.0
            do_sample = do_sample if do_sample is not None else False
            
            # Step 4: Generate SQL with T5 model
            logger.info("🤖 Generating SQL with T5 model...")
            
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
                    'early_stopping': True,
                    'no_repeat_ngram_size': 3,
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
            
            # Post-process to fix common issues
            generated_sql = self._clean_generated_sql(generated_sql)
            
            generation_time = time.time() - start_time
            
            # Update statistics
            self.generation_stats['total_queries'] += 1
            self.generation_stats['total_time'] += generation_time
            self.generation_stats['avg_time'] = self.generation_stats['total_time'] / self.generation_stats['total_queries']
            
            # Validate generated SQL
            validation_result = self._validate_sql(generated_sql)
            
            # Step 5: Fallback if needed
            if not validation_result['is_valid']:
                logger.warning(f"⚠️ T5 model generated invalid SQL, trying fallback generators...")
                
                # Try fallback generators
                intelligent_result = self.intelligent_fallback.generate_sql(nlq)
                basic_result = self.fallback_generator.generate_sql(nlq)
                
                # Choose the best fallback result
                fallback_result = None
                if (basic_result['validation']['is_valid'] and 
                    basic_result.get('confidence', 0) >= intelligent_result.get('confidence', 0)):
                    fallback_result = basic_result
                elif intelligent_result['validation']['is_valid']:
                    fallback_result = intelligent_result
                elif basic_result['validation']['is_valid']:
                    fallback_result = basic_result
                else:
                    fallback_result = basic_result  # Use as last resort
                
                if fallback_result['validation']['is_valid']:
                    self.generation_stats['successful_generations'] += 1
                    
                    result = {
                        'nlq': nlq,
                        'processed_nlq': processed_nlq,
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
                            'rag_enhanced': enhanced_query_info is not None and enhanced_query_info['rag_enhanced'],
                            'rag_info': enhanced_query_info,
                            'preprocessing': preprocessing_result
                        }
                    }
                    
                    return result
                else:
                    self.generation_stats['failed_generations'] += 1
            else:
                self.generation_stats['successful_generations'] += 1
                
                # Check if RAG improved the result
                if enhanced_query_info and enhanced_query_info['rag_enhanced']:
                    self.generation_stats['rag_improved_results'] += 1
            
            result = {
                'nlq': nlq,
                'processed_nlq': processed_nlq,
                'generated_sql': generated_sql,
                'generation_time': generation_time,
                'generation_config': generation_config,
                'validation': validation_result,
                'metadata': {
                    'method': 'rag_enhanced_t5' if (enhanced_query_info and enhanced_query_info['rag_enhanced']) else 't5_model',
                    'input_length': len(input_text),
                    'output_length': len(generated_sql),
                    'tokens_generated': len(outputs[0]),
                    'rag_enhanced': enhanced_query_info is not None and enhanced_query_info['rag_enhanced'],
                    'rag_info': enhanced_query_info,
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
                'processed_nlq': nlq,
                'generated_sql': '',
                'generation_time': generation_time,
                'error': str(e),
                'validation': {'is_valid': False, 'errors': [str(e)]},
                'metadata': {'error': True}
            }
    
    def generate_sql_with_gemini(self, 
                                nlq: str, 
                                use_rag: bool = True) -> Dict[str, Any]:
        """
        Generate SQL query directly using Gemini LLM (alternative to T5).
        
        Args:
            nlq: Natural language query
            use_rag: Whether to use RAG enhancement
            
        Returns:
            Dict containing generated SQL and metadata
        """
        if not self.rag_system.gemini_client or not self.rag_system.gemini_client.is_available():
            return {
                'nlq': nlq,
                'generated_sql': '',
                'generation_time': 0.0,
                'validation': {'is_valid': False, 'errors': ['Gemini not available']},
                'metadata': {
                    'method': 'gemini_unavailable',
                    'error': 'Gemini LLM not available'
                }
            }
        
        start_time = time.time()
        
        try:
            # Step 1: Get similar examples if RAG is enabled
            similar_examples = []
            if use_rag and self.rag_enabled:
                similar_examples = self.rag_system.retrieve_similar_examples(nlq, top_k=5)
                logger.info(f"🔍 Retrieved {len(similar_examples)} similar examples for Gemini")
            
            # Step 2: Generate SQL with Gemini
            schema_context = self._build_schema_context()
            gemini_result = self.rag_system.gemini_client.generate_sql_with_gemini(
                nlq, schema_context, similar_examples
            )
            
            generation_time = time.time() - start_time
            
            # Step 3: Validate the generated SQL
            generated_sql = gemini_result.get('generated_sql', '')
            validation_result = self._validate_sql(generated_sql)
            
            # Update statistics
            self.generation_stats['total_queries'] += 1
            self.generation_stats['total_time'] += generation_time
            
            if validation_result['is_valid']:
                self.generation_stats['successful_generations'] += 1
                if similar_examples:
                    self.generation_stats['rag_enhanced_queries'] += 1
                    self.generation_stats['rag_improved_results'] += 1
            else:
                self.generation_stats['failed_generations'] += 1
            
            result = {
                'nlq': nlq,
                'generated_sql': generated_sql,
                'generation_time': generation_time,
                'validation': validation_result,
                'metadata': {
                    'method': 'gemini_direct',
                    'rag_enhanced': len(similar_examples) > 0,
                    'similar_examples_used': len(similar_examples),
                    'gemini_info': gemini_result,
                    'confidence_score': gemini_result.get('confidence_score', 0.0)
                }
            }
            
            logger.info(f"✅ Gemini SQL generated in {generation_time:.3f}s: {generated_sql[:100]}...")
            
            return result
            
        except Exception as e:
            generation_time = time.time() - start_time
            self.generation_stats['total_queries'] += 1
            self.generation_stats['failed_generations'] += 1
            
            logger.error(f"❌ Error generating SQL with Gemini: {e}")
            
            return {
                'nlq': nlq,
                'generated_sql': '',
                'generation_time': generation_time,
                'validation': {'is_valid': False, 'errors': [str(e)]},
                'metadata': {
                    'method': 'gemini_error',
                    'error': str(e)
                }
            }
    
    def _build_schema_context(self) -> str:
        """Build schema context string to match the training data format."""
        return """Database Schema: clinical_data
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
    
    def _clean_generated_sql(self, sql: str) -> str:
        """Clean up common tokenization artifacts in generated SQL."""
        import re
        
        # Remove extra spaces around common SQL keywords and operators
        sql = re.sub(r'\s+', ' ', sql)
        sql = re.sub(r'\s*,\s*', ', ', sql)
        sql = re.sub(r'\s*\(\s*', '(', sql)
        sql = re.sub(r'\s*\)\s*', ')', sql)
        sql = re.sub(r'\s*=\s*', ' = ', sql)
        
        # Fix common column name issues with underscores
        sql = re.sub(r'start_\s+date', 'start_date', sql)
        sql = re.sub(r'stop_\s+date', 'stop_date', sql)
        sql = re.sub(r'first_\s+name', 'first_name', sql)
        sql = re.sub(r'last_\s+name', 'last_name', sql)
        sql = re.sub(r'patient_\s+id', 'patient_id', sql)
        
        return sql.strip()
    
    def _validate_sql(self, sql: str) -> Dict[str, Any]:
        """Validate generated SQL for basic correctness."""
        errors = []
        warnings = []
        
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
        
        is_valid = len(errors) == 0
        
        return {
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'has_schema_prefix': 'clinical_data.' in sql,
            'has_select': sql_upper.startswith('SELECT'),
            'has_from': 'FROM' in sql_upper,
            'sql_length': len(sql)
        }
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics including RAG performance."""
        stats = self.generation_stats.copy()
        
        # Add RAG-specific metrics
        if self.rag_enabled:
            rag_stats = self.rag_system.get_stats()
            stats['rag_stats'] = rag_stats
            
            if stats['total_queries'] > 0:
                stats['rag_enhancement_rate'] = stats['rag_enhanced_queries'] / stats['total_queries']
                stats['rag_improvement_rate'] = stats['rag_improved_results'] / max(stats['rag_enhanced_queries'], 1)
        
        return {
            **self.model_info,
            'generation_stats': stats,
            'rag_enabled': self.rag_enabled
        }
    
    def benchmark_rag_vs_traditional(self, test_queries: List[str]) -> Dict[str, Any]:
        """
        Benchmark RAG-enhanced vs traditional query processing.
        
        Args:
            test_queries: List of test queries
            
        Returns:
            Benchmark comparison results
        """
        logger.info("⚡ Benchmarking RAG vs Traditional processing")
        
        traditional_results = []
        rag_results = []
        
        # Test traditional approach
        logger.info("🔄 Testing traditional approach...")
        for query in test_queries:
            result = self.generate_sql(query, use_rag=False)
            traditional_results.append(result)
        
        # Test RAG approach
        logger.info("🔄 Testing RAG-enhanced approach...")
        for query in test_queries:
            result = self.generate_sql(query, use_rag=True)
            rag_results.append(result)
        
        # Compare results
        traditional_valid = sum(1 for r in traditional_results if r['validation']['is_valid'])
        rag_valid = sum(1 for r in rag_results if r['validation']['is_valid'])
        
        traditional_time = sum(r['generation_time'] for r in traditional_results)
        rag_time = sum(r['generation_time'] for r in rag_results)
        
        comparison = {
            'test_queries': test_queries,
            'traditional_results': {
                'valid_queries': traditional_valid,
                'total_queries': len(test_queries),
                'validity_rate': traditional_valid / len(test_queries),
                'avg_time': traditional_time / len(test_queries),
                'total_time': traditional_time
            },
            'rag_results': {
                'valid_queries': rag_valid,
                'total_queries': len(test_queries),
                'validity_rate': rag_valid / len(test_queries),
                'avg_time': rag_time / len(test_queries),
                'total_time': rag_time
            },
            'improvement': {
                'validity_improvement': (rag_valid - traditional_valid) / len(test_queries),
                'time_difference': (rag_time - traditional_time) / len(test_queries),
                'better_results': rag_valid > traditional_valid
            }
        }
        
        logger.info("✅ Benchmark completed")
        logger.info(f"Traditional: {traditional_valid}/{len(test_queries)} valid ({traditional_valid/len(test_queries)*100:.1f}%)")
        logger.info(f"RAG-Enhanced: {rag_valid}/{len(test_queries)} valid ({rag_valid/len(test_queries)*100:.1f}%)")
        
        return comparison