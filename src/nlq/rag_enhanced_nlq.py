#!/usr/bin/env python3
"""
RAG-Enhanced Natural Language Query System
Uses Retrieval-Augmented Generation to improve NLQ processing by:
1. Retrieving similar examples from training dataset
2. Using LLM to generate properly formatted queries
3. Providing better input to the T5 model
"""

import json
import logging
import numpy as np
import time
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import os
from datetime import datetime

# Optional LLM imports
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

try:
    from .gemini_llm_client import GeminiLLMClient
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    GeminiLLMClient = None

logger = logging.getLogger(__name__)

class RAGEnhancedNLQ:
    """
    RAG-Enhanced Natural Language Query system that improves T5 model performance
    by retrieving similar examples and using LLM to format queries properly.
    """
    
    def __init__(self, 
                 training_data_path: str = "d:/projects/healthca/data/processed/final_merged_dataset/train_data.json",
                 embedding_model: str = "all-MiniLM-L6-v2",
                 openai_api_key: Optional[str] = None,
                 gemini_api_key: Optional[str] = None,
                 preferred_llm: str = "gemini"):
        """
        Initialize the RAG-Enhanced NLQ system.
        
        Args:
            training_data_path: Path to training dataset
            embedding_model: Sentence transformer model for embeddings
            openai_api_key: OpenAI API key for LLM (optional, will try env var)
            gemini_api_key: Google Gemini API key for LLM (optional, will try env var)
            preferred_llm: Preferred LLM to use ('gemini', 'openai', or 'none')
        """
        self.training_data_path = training_data_path
        self.training_data = []
        self.query_embeddings = None
        self.embedding_model = None
        
        # Schema context that matches training format
        self.schema_context = """Database Schema: clinical_data
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
        
        # Initialize LLM clients
        self.preferred_llm = preferred_llm.lower()
        self.openai_client = None
        self.gemini_client = None
        
        # Initialize OpenAI (optional)
        if OPENAI_AVAILABLE and openai_api_key:
            openai.api_key = openai_api_key
            self.openai_client = openai
        elif OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
            openai.api_key = os.getenv('OPENAI_API_KEY')
            self.openai_client = openai
        
        # Initialize Gemini (optional)
        if GEMINI_AVAILABLE:
            self.gemini_client = GeminiLLMClient()
            if self.gemini_client.initialize(gemini_api_key):
                logger.info("✅ Gemini LLM client initialized")
            else:
                logger.info("ℹ️ Gemini LLM client not available")
                self.gemini_client = None
        
        # Statistics
        self.stats = {
            'total_queries': 0,
            'rag_enhanced_queries': 0,
            'llm_formatted_queries': 0,
            'retrieval_time': 0.0,
            'llm_time': 0.0,
            'total_time': 0.0
        }
        
        logger.info("🔧 RAG-Enhanced NLQ system initialized")
        
    def load_training_data(self) -> bool:
        """Load and prepare training data for RAG retrieval."""
        try:
            logger.info(f"📥 Loading training data from {self.training_data_path}")
            
            with open(self.training_data_path, 'r', encoding='utf-8') as f:
                self.training_data = json.load(f)
            
            logger.info(f"✅ Loaded {len(self.training_data)} training examples")
            
            # Extract natural language queries for embedding
            queries = []
            for example in self.training_data:
                # Extract the NLQ part from input_text
                input_text = example['input_text']
                nlq = input_text.split('Database Schema:')[0].replace('translate to sql: ', '').strip()
                queries.append(nlq)
            
            # Initialize embedding model
            logger.info("🔧 Loading sentence transformer model...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Create embeddings for all training queries
            logger.info("🔄 Creating embeddings for training queries...")
            self.query_embeddings = self.embedding_model.encode(queries)
            
            logger.info(f"✅ Created embeddings for {len(queries)} queries")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading training data: {e}")
            return False
    
    def retrieve_similar_examples(self, user_query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve similar examples from training data using semantic similarity.
        
        Args:
            user_query: User's natural language query
            top_k: Number of similar examples to retrieve
            
        Returns:
            List of similar examples with similarity scores
        """
        if not self.embedding_model or self.query_embeddings is None:
            logger.warning("⚠️ Training data not loaded, cannot retrieve examples")
            return []
        
        start_time = time.time()
        
        try:
            # Encode user query
            user_embedding = self.embedding_model.encode([user_query])
            
            # Calculate similarities
            similarities = cosine_similarity(user_embedding, self.query_embeddings)[0]
            
            # Get top-k most similar examples
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            similar_examples = []
            for idx in top_indices:
                example = self.training_data[idx].copy()
                example['similarity_score'] = float(similarities[idx])
                
                # Extract NLQ from input_text for clarity
                input_text = example['input_text']
                nlq = input_text.split('Database Schema:')[0].replace('translate to sql: ', '').strip()
                example['extracted_nlq'] = nlq
                
                similar_examples.append(example)
            
            retrieval_time = time.time() - start_time
            self.stats['retrieval_time'] += retrieval_time
            
            logger.info(f"🔍 Retrieved {len(similar_examples)} similar examples in {retrieval_time:.3f}s")
            
            return similar_examples
            
        except Exception as e:
            logger.error(f"❌ Error retrieving similar examples: {e}")
            return []
    
    def format_query_with_llm(self, user_query: str, similar_examples: List[Dict[str, Any]]) -> Optional[str]:
        """
        Use LLM to format the user query in the style of training examples.
        
        Args:
            user_query: Original user query
            similar_examples: Retrieved similar examples
            
        Returns:
            Formatted query or None if LLM not available
        """
        if not self.openai_client or not similar_examples:
            return None
        
        start_time = time.time()
        
        try:
            # Create prompt with examples
            examples_text = ""
            for i, example in enumerate(similar_examples[:3], 1):  # Use top 3 examples
                examples_text += f"\nExample {i}:\n"
                examples_text += f"User Query: {example['extracted_nlq']}\n"
                examples_text += f"Formatted Query: {example['extracted_nlq']}\n"
            
            prompt = f"""You are a clinical data query assistant. Your task is to reformat user queries to match the style and terminology used in our training examples.

Here are some similar examples from our training data:
{examples_text}

User's Query: "{user_query}"

Please reformat this query to match the style of the examples above. The query should:
1. Use clear, clinical terminology
2. Be specific about what data to retrieve
3. Match the phrasing style of the examples
4. Be concise but complete

Reformatted Query:"""

            response = self.openai_client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that reformats clinical queries to match training data style."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.3
            )
            
            formatted_query = response.choices[0].message.content.strip()
            
            llm_time = time.time() - start_time
            self.stats['llm_time'] += llm_time
            self.stats['llm_formatted_queries'] += 1
            
            logger.info(f"🤖 LLM formatted query in {llm_time:.3f}s")
            logger.info(f"   Original: {user_query}")
            logger.info(f"   Formatted: {formatted_query}")
            
            return formatted_query
            
        except Exception as e:
            logger.error(f"❌ Error formatting query with LLM: {e}")
            return None
    
    def enhance_query(self, user_query: str) -> Dict[str, Any]:
        """
        Enhance user query using RAG approach.
        
        Args:
            user_query: Original user query
            
        Returns:
            Enhanced query information
        """
        start_time = time.time()
        self.stats['total_queries'] += 1
        
        result = {
            'original_query': user_query,
            'enhanced_query': user_query,  # Default to original
            'similar_examples': [],
            'llm_formatted': False,
            'rag_enhanced': False,
            'confidence_score': 0.0,
            'processing_time': 0.0,
            'method_used': 'original'
        }
        
        try:
            # Step 1: Retrieve similar examples
            similar_examples = self.retrieve_similar_examples(user_query, top_k=5)
            result['similar_examples'] = similar_examples
            
            if similar_examples:
                result['rag_enhanced'] = True
                self.stats['rag_enhanced_queries'] += 1
                
                # Calculate confidence based on similarity scores
                avg_similarity = np.mean([ex['similarity_score'] for ex in similar_examples])
                result['confidence_score'] = float(avg_similarity)
                
                # Step 2: Try to format with LLM if available and similarity is high enough
                llm_result = None
                if avg_similarity > 0.7:
                    # Try preferred LLM first
                    if self.preferred_llm == 'gemini' and self.gemini_client:
                        llm_result = self.gemini_client.enhance_query_with_gemini(
                            user_query, similar_examples, self.schema_context
                        )
                        if llm_result and llm_result.get('enhanced_query'):
                            result['enhanced_query'] = llm_result['enhanced_query']
                            result['llm_formatted'] = True
                            result['method_used'] = 'rag_gemini_enhanced'
                            result['llm_info'] = llm_result
                    elif self.preferred_llm == 'openai' and self.openai_client:
                        formatted_query = self.format_query_with_llm(user_query, similar_examples)
                        if formatted_query:
                            result['enhanced_query'] = formatted_query
                            result['llm_formatted'] = True
                            result['method_used'] = 'rag_openai_enhanced'
                    
                    # Fallback to other LLM if preferred one failed
                    if not result['llm_formatted']:
                        if self.gemini_client and self.preferred_llm != 'gemini':
                            llm_result = self.gemini_client.enhance_query_with_gemini(
                                user_query, similar_examples, self.schema_context
                            )
                            if llm_result and llm_result.get('enhanced_query'):
                                result['enhanced_query'] = llm_result['enhanced_query']
                                result['llm_formatted'] = True
                                result['method_used'] = 'rag_gemini_fallback'
                                result['llm_info'] = llm_result
                        elif self.openai_client and self.preferred_llm != 'openai':
                            formatted_query = self.format_query_with_llm(user_query, similar_examples)
                            if formatted_query:
                                result['enhanced_query'] = formatted_query
                                result['llm_formatted'] = True
                                result['method_used'] = 'rag_openai_fallback'
                
                if not result['llm_formatted']:
                    result['method_used'] = 'rag_enhanced'
                else:
                    # Use the most similar example as guidance for enhancement
                    best_example = similar_examples[0]
                    if best_example['similarity_score'] > 0.8:
                        # High similarity - use similar phrasing
                        result['enhanced_query'] = self._enhance_with_similar_phrasing(
                            user_query, best_example['extracted_nlq']
                        )
                        result['method_used'] = 'rag_similarity_enhanced'
                    else:
                        result['method_used'] = 'rag_retrieved_only'
            
            processing_time = time.time() - start_time
            result['processing_time'] = processing_time
            self.stats['total_time'] += processing_time
            
            logger.info(f"✅ Query enhanced using {result['method_used']} in {processing_time:.3f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error enhancing query: {e}")
            result['error'] = str(e)
            return result
    
    def _enhance_with_similar_phrasing(self, user_query: str, similar_query: str) -> str:
        """
        Enhance user query by adapting phrasing from similar query.
        
        Args:
            user_query: Original user query
            similar_query: Similar query from training data
            
        Returns:
            Enhanced query
        """
        # Simple enhancement - this could be made more sophisticated
        enhanced = user_query
        
        # Common enhancements based on training data patterns
        if 'how many' in user_query.lower() and 'patients' in user_query.lower():
            if 'how many patients' not in user_query.lower():
                enhanced = user_query.replace('how many', 'How many patients')
        
        if 'show' in user_query.lower() and 'patients' in user_query.lower():
            if not user_query.lower().startswith('show'):
                enhanced = f"Show {user_query.lower()}"
        
        if 'list' in user_query.lower():
            if not user_query.lower().startswith('list'):
                enhanced = f"List {user_query.lower().replace('list', '').strip()}"
        
        return enhanced
    
    def create_formatted_input(self, enhanced_query: str) -> str:
        """
        Create properly formatted input for T5 model matching training format.
        
        Args:
            enhanced_query: Enhanced query
            
        Returns:
            Formatted input text for T5 model
        """
        return f"translate to sql: {enhanced_query} {self.schema_context}"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get RAG system statistics."""
        stats = self.stats.copy()
        if stats['total_queries'] > 0:
            stats['rag_enhancement_rate'] = stats['rag_enhanced_queries'] / stats['total_queries']
            stats['llm_formatting_rate'] = stats['llm_formatted_queries'] / stats['total_queries']
            stats['avg_retrieval_time'] = stats['retrieval_time'] / stats['total_queries']
            stats['avg_llm_time'] = stats['llm_time'] / max(stats['llm_formatted_queries'], 1)
            stats['avg_total_time'] = stats['total_time'] / stats['total_queries']
        
        return stats
    
    def reset_stats(self):
        """Reset statistics."""
        self.stats = {
            'total_queries': 0,
            'rag_enhanced_queries': 0,
            'llm_formatted_queries': 0,
            'retrieval_time': 0.0,
            'llm_time': 0.0,
            'total_time': 0.0
        }
        logger.info("📊 RAG statistics reset")

# Example usage and testing
if __name__ == "__main__":
    # Test the RAG system
    rag_system = RAGEnhancedNLQ()
    
    if rag_system.load_training_data():
        # Test queries
        test_queries = [
            "How many patients are there?",
            "Show me diabetic patients",
            "List medications for hypertension",
            "Find high cost patients",
            "What providers are in Boston?"
        ]
        
        print("🧪 Testing RAG-Enhanced NLQ System")
        print("=" * 50)
        
        for query in test_queries:
            print(f"\n🔍 Testing: {query}")
            result = rag_system.enhance_query(query)
            
            print(f"   Enhanced: {result['enhanced_query']}")
            print(f"   Method: {result['method_used']}")
            print(f"   Confidence: {result['confidence_score']:.3f}")
            print(f"   Time: {result['processing_time']:.3f}s")
            
            if result['similar_examples']:
                print(f"   Similar examples found: {len(result['similar_examples'])}")
                for i, ex in enumerate(result['similar_examples'][:2], 1):
                    print(f"     {i}. {ex['extracted_nlq']} (sim: {ex['similarity_score']:.3f})")
        
        print(f"\n📊 Final Statistics:")
        stats = rag_system.get_stats()
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.3f}")
            else:
                print(f"   {key}: {value}")