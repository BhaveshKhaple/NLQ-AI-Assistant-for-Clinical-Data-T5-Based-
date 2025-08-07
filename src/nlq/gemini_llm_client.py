#!/usr/bin/env python3
"""
Google Gemini LLM Client
Provides integration with Google Gemini API for enhanced query processing.
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

# from .config_loader import ConfigLoader  # Not needed for basic functionality

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiLLMClient:
    """Google Gemini LLM client for clinical query processing."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize Gemini client."""
        # Use default configuration
        self.config = {
            'gemini': {
                'model_name': 'gemini-1.5-flash',
                'temperature': 0.1,
                'top_p': 0.8,
                'top_k': 40,
                'max_output_tokens': 2048
            }
        }
        self.model = None
        self.api_key = None
        self.model_name = "gemini-1.5-flash"  # Default model
        self.initialized = False
        
        # Gemini-specific settings
        self.generation_config = {
            "temperature": 0.1,  # Low temperature for consistent SQL generation
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
        
        # Safety settings for medical content
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        logger.info("🔧 Gemini LLM Client initialized")
    
    def initialize(self, api_key: Optional[str] = None) -> bool:
        """Initialize Gemini API connection."""
        if not GEMINI_AVAILABLE:
            logger.error("❌ Google Generative AI library not installed. Install with: pip install google-generativeai")
            return False
        
        try:
            # Get API key
            self.api_key = api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            
            if not self.api_key:
                logger.warning("⚠️ No Gemini API key found. Set GEMINI_API_KEY environment variable.")
                return False
            
            # Configure Gemini
            genai.configure(api_key=self.api_key)
            
            # Initialize model
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            # Test connection
            test_response = self.model.generate_content("Hello")
            if test_response and test_response.text:
                self.initialized = True
                logger.info("✅ Gemini API initialized successfully")
                logger.info(f"🤖 Using model: {self.model_name}")
                return True
            else:
                logger.error("❌ Gemini API test failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Gemini initialization error: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if Gemini is available and initialized."""
        return GEMINI_AVAILABLE and self.initialized and self.model is not None
    
    def enhance_query_with_gemini(self, 
                                  original_query: str, 
                                  similar_examples: List[Dict],
                                  schema_context: Optional[str] = None) -> Dict[str, Any]:
        """Enhance query using Gemini LLM with RAG context."""
        if not self.is_available():
            return {
                'enhanced_query': original_query,
                'method_used': 'gemini_unavailable',
                'confidence_score': 0.0,
                'processing_time': 0.0,
                'error': 'Gemini not available'
            }
        
        start_time = time.time()
        
        try:
            # Build context from similar examples
            examples_context = self._build_examples_context(similar_examples)
            
            # Create enhancement prompt
            prompt = self._create_enhancement_prompt(
                original_query, 
                examples_context, 
                schema_context
            )
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                enhanced_query = self._extract_enhanced_query(response.text)
                confidence = self._calculate_confidence(original_query, enhanced_query, similar_examples)
                
                processing_time = time.time() - start_time
                
                return {
                    'enhanced_query': enhanced_query,
                    'method_used': 'gemini_enhanced',
                    'confidence_score': confidence,
                    'processing_time': processing_time,
                    'gemini_response': response.text,
                    'similar_examples_used': len(similar_examples)
                }
            else:
                logger.warning("⚠️ Empty response from Gemini")
                return self._fallback_response(original_query, start_time)
                
        except Exception as e:
            logger.error(f"❌ Gemini enhancement error: {e}")
            return self._fallback_response(original_query, start_time, str(e))
    
    def generate_sql_with_gemini(self, 
                                 query: str, 
                                 schema_context: str,
                                 similar_examples: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Generate SQL directly using Gemini LLM."""
        if not self.is_available():
            return {
                'generated_sql': '',
                'method_used': 'gemini_unavailable',
                'confidence_score': 0.0,
                'processing_time': 0.0,
                'error': 'Gemini not available'
            }
        
        start_time = time.time()
        
        try:
            # Build examples context if provided
            examples_context = ""
            if similar_examples:
                examples_context = self._build_sql_examples_context(similar_examples)
            
            # Create SQL generation prompt
            prompt = self._create_sql_generation_prompt(query, schema_context, examples_context)
            
            # Generate SQL
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                sql = self._extract_sql_from_response(response.text)
                confidence = self._calculate_sql_confidence(sql)
                
                processing_time = time.time() - start_time
                
                return {
                    'generated_sql': sql,
                    'method_used': 'gemini_sql_generation',
                    'confidence_score': confidence,
                    'processing_time': processing_time,
                    'gemini_response': response.text,
                    'examples_used': len(similar_examples) if similar_examples else 0
                }
            else:
                logger.warning("⚠️ Empty SQL response from Gemini")
                return self._fallback_sql_response(start_time)
                
        except Exception as e:
            logger.error(f"❌ Gemini SQL generation error: {e}")
            return self._fallback_sql_response(start_time, str(e))
    
    def _build_examples_context(self, similar_examples: List[Dict]) -> str:
        """Build context string from similar examples."""
        if not similar_examples:
            return ""
        
        context = "Similar successful queries from training data:\n\n"
        
        for i, example in enumerate(similar_examples[:3], 1):  # Use top 3 examples
            nlq = example.get('extracted_nlq', '')
            sql = example.get('target_text', '')
            similarity = example.get('similarity_score', 0.0)
            
            context += f"Example {i} (similarity: {similarity:.3f}):\n"
            context += f"Query: {nlq}\n"
            context += f"SQL: {sql}\n\n"
        
        return context
    
    def _build_sql_examples_context(self, similar_examples: List[Dict]) -> str:
        """Build SQL examples context for direct SQL generation."""
        if not similar_examples:
            return ""
        
        context = "Here are similar successful SQL examples:\n\n"
        
        for i, example in enumerate(similar_examples[:5], 1):  # Use top 5 for SQL
            nlq = example.get('extracted_nlq', '')
            sql = example.get('target_text', '')
            similarity = example.get('similarity_score', 0.0)
            
            context += f"Example {i}:\n"
            context += f"Natural Language: {nlq}\n"
            context += f"SQL: {sql}\n"
            context += f"Similarity: {similarity:.3f}\n\n"
        
        return context
    
    def _create_enhancement_prompt(self, 
                                   original_query: str, 
                                   examples_context: str,
                                   schema_context: Optional[str] = None) -> str:
        """Create prompt for query enhancement."""
        prompt = f"""You are a clinical data query enhancement expert. Your task is to improve natural language queries for better SQL generation.

Original Query: "{original_query}"

{examples_context}

Database Schema Context:
{schema_context or "Clinical database with patients, encounters, conditions, medications, procedures tables."}

Instructions:
1. Analyze the original query and similar examples
2. Enhance the query to be more specific and SQL-friendly
3. Use medical terminology consistently
4. Ensure the enhanced query maintains the original intent
5. Make it clear and unambiguous for SQL generation

Enhanced Query:"""
        
        return prompt
    
    def _create_sql_generation_prompt(self, 
                                      query: str, 
                                      schema_context: str,
                                      examples_context: str = "") -> str:
        """Create prompt for direct SQL generation."""
        prompt = f"""You are an expert SQL generator for clinical databases. Generate accurate SQL queries from natural language.

Natural Language Query: "{query}"

Database Schema:
{schema_context}

{examples_context}

Instructions:
1. Generate a valid PostgreSQL query
2. Use proper JOINs for related tables
3. Include appropriate WHERE clauses
4. Use DISTINCT when needed to avoid duplicates
5. Follow the patterns from similar examples
6. Return only the SQL query, no explanations

SQL Query:"""
        
        return prompt
    
    def _extract_enhanced_query(self, response_text: str) -> str:
        """Extract enhanced query from Gemini response."""
        # Look for the enhanced query in the response
        lines = response_text.strip().split('\n')
        
        # Try to find the last non-empty line (likely the enhanced query)
        for line in reversed(lines):
            line = line.strip()
            if line and not line.startswith(('Enhanced Query:', 'Query:', 'Result:')):
                return line
        
        # If no clear enhanced query found, return the cleaned response
        return response_text.strip()
    
    def _extract_sql_from_response(self, response_text: str) -> str:
        """Extract SQL query from Gemini response."""
        # Remove markdown code blocks if present
        text = response_text.strip()
        
        # Remove ```sql and ``` markers
        if '```sql' in text:
            text = text.split('```sql')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()
        
        # Clean up the SQL
        lines = text.split('\n')
        sql_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith(('--', '#', '//')):  # Skip comments
                sql_lines.append(line)
        
        return ' '.join(sql_lines)
    
    def _calculate_confidence(self, 
                              original_query: str, 
                              enhanced_query: str, 
                              similar_examples: List[Dict]) -> float:
        """Calculate confidence score for enhancement."""
        if not similar_examples:
            return 0.5
        
        # Base confidence on similarity scores of examples used
        similarities = [ex.get('similarity_score', 0.0) for ex in similar_examples[:3]]
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
        
        # Adjust based on enhancement (if query was changed significantly)
        enhancement_factor = 0.9 if enhanced_query != original_query else 0.8
        
        return min(avg_similarity * enhancement_factor, 1.0)
    
    def _calculate_sql_confidence(self, sql: str) -> float:
        """Calculate confidence score for generated SQL."""
        if not sql:
            return 0.0
        
        # Basic SQL validation checks
        sql_lower = sql.lower()
        confidence = 0.5  # Base confidence
        
        # Check for essential SQL components
        if 'select' in sql_lower:
            confidence += 0.2
        if 'from' in sql_lower:
            confidence += 0.2
        if any(keyword in sql_lower for keyword in ['join', 'where', 'group by', 'order by']):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _fallback_response(self, 
                           original_query: str, 
                           start_time: float, 
                           error: Optional[str] = None) -> Dict[str, Any]:
        """Create fallback response when Gemini fails."""
        return {
            'enhanced_query': original_query,
            'method_used': 'gemini_fallback',
            'confidence_score': 0.0,
            'processing_time': time.time() - start_time,
            'error': error
        }
    
    def _fallback_sql_response(self, 
                               start_time: float, 
                               error: Optional[str] = None) -> Dict[str, Any]:
        """Create fallback response when Gemini SQL generation fails."""
        return {
            'generated_sql': '',
            'method_used': 'gemini_sql_fallback',
            'confidence_score': 0.0,
            'processing_time': time.time() - start_time,
            'error': error
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the Gemini model."""
        return {
            'model_name': self.model_name,
            'available': self.is_available(),
            'initialized': self.initialized,
            'generation_config': self.generation_config,
            'api_key_set': bool(self.api_key)
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Gemini API connection."""
        if not self.is_available():
            return {
                'success': False,
                'error': 'Gemini not available or not initialized'
            }
        
        try:
            start_time = time.time()
            response = self.model.generate_content("Test connection")
            response_time = time.time() - start_time
            
            return {
                'success': True,
                'response_time': response_time,
                'model': self.model_name,
                'response_length': len(response.text) if response and response.text else 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }