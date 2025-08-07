#!/usr/bin/env python3
"""
Gemini RAG API Client
Simple client for interacting with the Gemini RAG API.
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class QueryResult:
    """Result from API query."""
    success: bool
    query: str
    generated_sql: str
    method_used: str
    generation_time: float
    confidence_score: float
    validation: Dict[str, Any]
    similar_examples: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class GeminiRAGAPIClient:
    """Client for the Gemini RAG API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize API client."""
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def query(self, 
              query: str,
              use_rag: bool = True,
              method: str = "t5_enhanced",
              max_length: int = 512,
              temperature: float = 0.1,
              include_examples: bool = True) -> QueryResult:
        """Process a natural language query."""
        try:
            payload = {
                "query": query,
                "use_rag": use_rag,
                "method": method,
                "max_length": max_length,
                "temperature": temperature,
                "include_examples": include_examples
            }
            
            response = self.session.post(f"{self.base_url}/query", json=payload)
            response.raise_for_status()
            
            data = response.json()
            return QueryResult(**data)
            
        except Exception as e:
            return QueryResult(
                success=False,
                query=query,
                generated_sql="",
                method_used="error",
                generation_time=0.0,
                confidence_score=0.0,
                validation={"is_valid": False, "errors": [str(e)]},
                error=str(e)
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get API statistics."""
        try:
            response = self.session.get(f"{self.base_url}/stats")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_similar_examples(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Get similar examples for a query."""
        try:
            response = self.session.get(f"{self.base_url}/examples/{query}?top_k={top_k}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def enhance_query(self, query: str) -> Dict[str, Any]:
        """Enhance a query using RAG."""
        try:
            payload = {"query": query}
            response = self.session.post(f"{self.base_url}/enhance", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def test_gemini(self) -> Dict[str, Any]:
        """Test Gemini connection."""
        try:
            response = self.session.post(f"{self.base_url}/gemini/test")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def batch_query(self, queries: List[str], **kwargs) -> List[QueryResult]:
        """Process multiple queries."""
        results = []
        for query in queries:
            result = self.query(query, **kwargs)
            results.append(result)
            time.sleep(0.1)  # Small delay to avoid overwhelming the API
        return results

# Example usage and testing
def main():
    """Example usage of the API client."""
    print("🧪 Testing Gemini RAG API Client")
    print("=" * 50)
    
    # Initialize client
    client = GeminiRAGAPIClient()
    
    # Health check
    print("\n📊 Health Check:")
    health = client.health_check()
    print(json.dumps(health, indent=2))
    
    if health.get("status") != "healthy":
        print("⚠️ API not healthy, some tests may fail")
    
    # Test queries
    test_queries = [
        "How many patients are there?",
        "Show me diabetic patients",
        "What medications are prescribed for hypertension?",
        "List all procedures performed in 2023"
    ]
    
    print(f"\n🔍 Testing {len(test_queries)} queries:")
    print("-" * 30)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: {query}")
        
        # Test with different methods
        methods = ["t5_enhanced", "gemini_direct", "hybrid"]
        
        for method in methods:
            print(f"   Method: {method}")
            result = client.query(query, method=method)
            
            if result.success:
                print(f"   ✅ Success: {result.generated_sql[:100]}...")
                print(f"   ⏱️ Time: {result.generation_time:.3f}s")
                print(f"   🎯 Confidence: {result.confidence_score:.3f}")
            else:
                print(f"   ❌ Failed: {result.error}")
    
    # Test similar examples
    print(f"\n📚 Testing similar examples:")
    examples = client.get_similar_examples("Show me patients with diabetes")
    if "error" not in examples:
        print(f"   Found {examples.get('count', 0)} similar examples")
        for ex in examples.get('similar_examples', [])[:2]:
            print(f"   - {ex.get('extracted_nlq', 'N/A')} (sim: {ex.get('similarity_score', 0):.3f})")
    else:
        print(f"   ❌ Error: {examples['error']}")
    
    # Test query enhancement
    print(f"\n✨ Testing query enhancement:")
    enhancement = client.enhance_query("Show diabetic patients")
    if "error" not in enhancement:
        print(f"   Original: {enhancement.get('original_query', 'N/A')}")
        print(f"   Enhanced: {enhancement.get('enhanced_query', 'N/A')}")
        print(f"   Method: {enhancement.get('method_used', 'N/A')}")
    else:
        print(f"   ❌ Error: {enhancement['error']}")
    
    # Get statistics
    print(f"\n📈 API Statistics:")
    stats = client.get_statistics()
    if "error" not in stats:
        print(f"   Total queries: {stats.get('total_queries', 0)}")
        print(f"   Success rate: {stats.get('successful_queries', 0)}/{stats.get('total_queries', 0)}")
        print(f"   Avg response time: {stats.get('average_response_time', 0):.3f}s")
        print(f"   RAG enhancement rate: {stats.get('rag_enhancement_rate', 0)*100:.1f}%")
        print(f"   Gemini available: {stats.get('gemini_availability', False)}")
    else:
        print(f"   ❌ Error: {stats['error']}")
    
    print("\n🎉 API client testing complete!")

if __name__ == "__main__":
    main()