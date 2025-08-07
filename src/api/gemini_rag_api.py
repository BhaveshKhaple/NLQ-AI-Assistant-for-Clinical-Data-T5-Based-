#!/usr/bin/env python3
"""
Gemini RAG API Server
FastAPI-based REST API for the Gemini-enhanced RAG Clinical NLQ system.
"""

import os
import sys
import time
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from nlq.rag_inference_engine import RAGEnhancedInferenceEngine
from nlq.gemini_llm_client import GeminiLLMClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Gemini RAG Clinical NLQ API",
    description="REST API for Gemini-enhanced RAG Clinical Natural Language Query processing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for model instances
rag_engine: Optional[RAGEnhancedInferenceEngine] = None
gemini_client: Optional[GeminiLLMClient] = None

# Pydantic models for API requests/responses
class QueryRequest(BaseModel):
    """Request model for query processing."""
    query: str = Field(..., description="Natural language query", min_length=1, max_length=1000)
    use_rag: bool = Field(True, description="Whether to use RAG enhancement")
    method: str = Field("t5_enhanced", description="SQL generation method: t5_enhanced, gemini_direct, hybrid")
    max_length: Optional[int] = Field(512, description="Maximum SQL length")
    temperature: Optional[float] = Field(0.1, description="Generation temperature")
    include_examples: bool = Field(True, description="Include similar examples in response")

class QueryResponse(BaseModel):
    """Response model for query processing."""
    success: bool
    query: str
    generated_sql: str
    method_used: str
    generation_time: float
    confidence_score: float
    validation: Dict[str, Any]
    similar_examples: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any]
    error: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    services: Dict[str, Any]

class StatsResponse(BaseModel):
    """Statistics response."""
    total_queries: int
    successful_queries: int
    failed_queries: int
    average_response_time: float
    rag_enhancement_rate: float
    gemini_availability: bool
    uptime: str

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize models on startup."""
    global rag_engine, gemini_client
    
    logger.info("🚀 Starting Gemini RAG API server...")
    
    try:
        # Initialize RAG engine
        rag_engine = RAGEnhancedInferenceEngine()
        
        # Load T5 model
        if rag_engine.load_model():
            logger.info("✅ T5 model loaded successfully")
        else:
            logger.warning("⚠️ T5 model loading failed")
        
        # Initialize RAG system
        if rag_engine.initialize_rag_system():
            logger.info("✅ RAG system initialized successfully")
        else:
            logger.warning("⚠️ RAG system initialization failed")
        
        # Initialize Gemini client
        gemini_client = GeminiLLMClient()
        if gemini_client.initialize():
            logger.info("✅ Gemini client initialized successfully")
        else:
            logger.warning("⚠️ Gemini client initialization failed")
        
        logger.info("🎉 API server startup complete!")
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        raise

# Dependency to get RAG engine
def get_rag_engine() -> RAGEnhancedInferenceEngine:
    """Get RAG engine instance."""
    if rag_engine is None:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")
    return rag_engine

# Dependency to get Gemini client
def get_gemini_client() -> GeminiLLMClient:
    """Get Gemini client instance."""
    if gemini_client is None or not gemini_client.is_available():
        raise HTTPException(status_code=503, detail="Gemini client not available")
    return gemini_client

# API Endpoints

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {
        "message": "Gemini RAG Clinical NLQ API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    services = {
        "rag_engine": {
            "status": "available" if rag_engine else "unavailable",
            "model_loaded": rag_engine.model is not None if rag_engine else False,
            "rag_initialized": rag_engine.rag_enabled if rag_engine else False
        },
        "gemini_client": {
            "status": "available" if gemini_client and gemini_client.is_available() else "unavailable",
            "initialized": gemini_client.initialized if gemini_client else False
        }
    }
    
    overall_status = "healthy" if all(
        service["status"] == "available" for service in services.values()
    ) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now().isoformat(),
        services=services
    )

@app.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    engine: RAGEnhancedInferenceEngine = Depends(get_rag_engine)
):
    """Process a natural language query."""
    start_time = time.time()
    
    try:
        logger.info(f"📝 Processing query: {request.query[:100]}...")
        
        # Choose processing method
        if request.method == "gemini_direct":
            # Use Gemini directly
            result = engine.generate_sql_with_gemini(
                request.query,
                use_rag=request.use_rag
            )
        elif request.method == "hybrid":
            # Try Gemini first, fallback to T5
            try:
                result = engine.generate_sql_with_gemini(
                    request.query,
                    use_rag=request.use_rag
                )
                if not result['validation']['is_valid']:
                    # Fallback to T5
                    result = engine.generate_sql(
                        request.query,
                        use_rag=request.use_rag,
                        max_length=request.max_length,
                        temperature=request.temperature
                    )
                    result['metadata']['method'] = 'hybrid_t5_fallback'
            except Exception:
                # Fallback to T5 on error
                result = engine.generate_sql(
                    request.query,
                    use_rag=request.use_rag,
                    max_length=request.max_length,
                    temperature=request.temperature
                )
                result['metadata']['method'] = 'hybrid_t5_fallback'
        else:
            # Default: T5 enhanced
            result = engine.generate_sql(
                request.query,
                use_rag=request.use_rag,
                max_length=request.max_length,
                temperature=request.temperature
            )
        
        # Get similar examples if requested
        similar_examples = None
        if request.include_examples and request.use_rag:
            try:
                similar_examples = engine.rag_system.retrieve_similar_examples(
                    request.query, top_k=3
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to retrieve examples: {e}")
        
        # Prepare response
        response = QueryResponse(
            success=result['validation']['is_valid'],
            query=request.query,
            generated_sql=result['generated_sql'],
            method_used=result['metadata'].get('method', 'unknown'),
            generation_time=result['generation_time'],
            confidence_score=result['metadata'].get('confidence_score', 0.0),
            validation=result['validation'],
            similar_examples=similar_examples,
            metadata=result['metadata']
        )
        
        processing_time = time.time() - start_time
        logger.info(f"✅ Query processed in {processing_time:.3f}s")
        
        # Log query in background
        background_tasks.add_task(
            log_query_async,
            request.query,
            result['generated_sql'],
            result['validation']['is_valid'],
            processing_time
        )
        
        return response
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ Query processing error: {e}")
        
        return QueryResponse(
            success=False,
            query=request.query,
            generated_sql="",
            method_used="error",
            generation_time=processing_time,
            confidence_score=0.0,
            validation={"is_valid": False, "errors": [str(e)]},
            metadata={"error": str(e)},
            error=str(e)
        )

@app.get("/stats", response_model=StatsResponse)
async def get_statistics(engine: RAGEnhancedInferenceEngine = Depends(get_rag_engine)):
    """Get system statistics."""
    try:
        stats = engine.get_comprehensive_stats()
        gen_stats = stats.get('generation_stats', {})
        
        return StatsResponse(
            total_queries=gen_stats.get('total_queries', 0),
            successful_queries=gen_stats.get('successful_generations', 0),
            failed_queries=gen_stats.get('failed_generations', 0),
            average_response_time=gen_stats.get('avg_time', 0.0),
            rag_enhancement_rate=gen_stats.get('rag_enhancement_rate', 0.0),
            gemini_availability=gemini_client.is_available() if gemini_client else False,
            uptime=str(datetime.now() - datetime.now())  # Placeholder
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {e}")

@app.post("/gemini/test")
async def test_gemini(client: GeminiLLMClient = Depends(get_gemini_client)):
    """Test Gemini connection."""
    try:
        test_result = client.test_connection()
        return test_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini test failed: {e}")

@app.get("/examples/{query}")
async def get_similar_examples(
    query: str,
    top_k: int = 5,
    engine: RAGEnhancedInferenceEngine = Depends(get_rag_engine)
):
    """Get similar examples for a query."""
    try:
        if not engine.rag_enabled:
            raise HTTPException(status_code=503, detail="RAG system not enabled")
        
        examples = engine.rag_system.retrieve_similar_examples(query, top_k=top_k)
        return {
            "query": query,
            "similar_examples": examples,
            "count": len(examples)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve examples: {e}")

@app.post("/enhance")
async def enhance_query(
    request: Dict[str, str],
    engine: RAGEnhancedInferenceEngine = Depends(get_rag_engine)
):
    """Enhance a query using RAG."""
    try:
        query = request.get("query")
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        if not engine.rag_enabled:
            raise HTTPException(status_code=503, detail="RAG system not enabled")
        
        enhancement_result = engine.rag_system.enhance_query(query)
        return enhancement_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enhance query: {e}")

# Background task for logging
async def log_query_async(query: str, sql: str, success: bool, processing_time: float):
    """Log query asynchronously."""
    try:
        # Implement your logging logic here
        logger.info(f"📊 Query logged: success={success}, time={processing_time:.3f}s")
    except Exception as e:
        logger.error(f"❌ Logging error: {e}")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"❌ Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "status_code": 500}
    )

# Main function to run the server
def main():
    """Run the API server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Gemini RAG Clinical NLQ API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    
    args = parser.parse_args()
    
    logger.info(f"🚀 Starting Gemini RAG API server on {args.host}:{args.port}")
    
    uvicorn.run(
        "gemini_rag_api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level="info"
    )

if __name__ == "__main__":
    main()