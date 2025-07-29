#!/usr/bin/env python3
"""
Inference Pipeline
Main orchestrator that links user queries to results through the trained T5 model and database.
"""

import time
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from .inference_engine import ClinicalInferenceEngine
from .database_executor import DatabaseExecutor
from .result_formatter import ResultFormatter
from .logging_system import InferenceLogger, get_logger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InferencePipeline:
    """
    Main inference pipeline that orchestrates the complete process:
    1. Load T5 model and tokenizer
    2. Convert natural language to SQL
    3. Execute SQL against database
    4. Format results for output
    5. Log all activities
    """
    
    def __init__(self, 
                 config_path: str = "d:/projects/healthca/config/config.yaml",
                 model_path: Optional[str] = None,
                 auto_connect: bool = True):
        """
        Initialize the inference pipeline.
        
        Args:
            config_path: Path to configuration file
            model_path: Path to trained model (optional)
            auto_connect: Whether to automatically connect to database
        """
        self.config_path = config_path
        self.model_path = model_path
        
        # Initialize components
        self.inference_engine = ClinicalInferenceEngine(config_path)
        self.database_executor = DatabaseExecutor(config_path)
        self.result_formatter = ResultFormatter(config_path)
        self.logger = get_logger()
        
        # Pipeline state
        self.is_initialized = False
        self.model_loaded = False
        self.database_connected = False
        
        # Pipeline statistics
        self.pipeline_stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'avg_total_time': 0.0,
            'avg_generation_time': 0.0,
            'avg_execution_time': 0.0,
            'avg_formatting_time': 0.0,
            'error_breakdown': {},
            'initialization_time': None
        }
        
        # Initialize pipeline
        if auto_connect:
            self.initialize()
    
    def initialize(self) -> Dict[str, Any]:
        """
        Initialize the complete pipeline.
        
        Returns:
            Dict with initialization results
        """
        start_time = time.time()
        
        try:
            logger.info("🚀 Initializing Clinical NLQ Inference Pipeline")
            
            # Log system information
            system_info = {
                'config_path': self.config_path,
                'model_path': self.model_path,
                'components': ['inference_engine', 'database_executor', 'result_formatter']
            }
            self.logger.log_system_info(system_info)
            
            # Initialize inference engine (load model)
            logger.info("📥 Loading T5 model...")
            model_loaded = self.inference_engine.load_model(self.model_path)
            if not model_loaded:
                raise RuntimeError("Failed to load T5 model")
            
            self.model_loaded = True
            logger.info("✅ T5 model loaded successfully")
            
            # Connect to database
            logger.info("🔌 Connecting to database...")
            db_connected = self.database_executor.connect()
            if not db_connected:
                raise RuntimeError("Failed to connect to database")
            
            self.database_connected = True
            logger.info("✅ Database connected successfully")
            
            # Test database connection
            connection_test = self.database_executor.test_connection()
            if not connection_test.get('success', False):
                logger.warning("⚠️ Database connection test failed")
            
            initialization_time = time.time() - start_time
            self.pipeline_stats['initialization_time'] = initialization_time
            self.is_initialized = True
            
            # Get component information
            model_info = self.inference_engine.get_model_info()
            schema_info = self.database_executor.get_schema_info()
            
            result = {
                'success': True,
                'initialization_time': initialization_time,
                'model_loaded': self.model_loaded,
                'database_connected': self.database_connected,
                'model_info': model_info,
                'database_info': {
                    'connection_test': connection_test,
                    'schema_summary': {
                        'total_tables': schema_info.get('total_tables', 0),
                        'total_columns': schema_info.get('total_columns', 0)
                    }
                },
                'pipeline_ready': self.is_initialized
            }
            
            logger.info(f"🎉 Pipeline initialized successfully in {initialization_time:.3f}s")
            return result
            
        except Exception as e:
            initialization_time = time.time() - start_time
            self.pipeline_stats['initialization_time'] = initialization_time
            
            self.logger.log_error(e, {
                'component': 'pipeline_initialization',
                'initialization_time': initialization_time
            })
            
            logger.error(f"❌ Pipeline initialization failed: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'initialization_time': initialization_time,
                'model_loaded': self.model_loaded,
                'database_connected': self.database_connected,
                'pipeline_ready': False
            }
    
    def process_query(self, 
                     nlq: str,
                     output_formats: List[str] = None,
                     user_id: Optional[str] = None,
                     session_info: Optional[Dict[str, Any]] = None,
                     generation_params: Optional[Dict[str, Any]] = None,
                     execution_params: Optional[Dict[str, Any]] = None,
                     format_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a complete natural language query through the pipeline.
        
        Args:
            nlq: Natural language query
            output_formats: List of desired output formats
            user_id: User identifier for logging
            session_info: Additional session information
            generation_params: Parameters for SQL generation
            execution_params: Parameters for database execution
            format_params: Parameters for result formatting
            
        Returns:
            Dict with complete query results
        """
        if not self.is_initialized:
            return {
                'success': False,
                'error': 'Pipeline not initialized. Call initialize() first.',
                'pipeline_ready': False
            }
        
        # Set defaults
        output_formats = output_formats or ['table']
        generation_params = generation_params or {}
        execution_params = execution_params or {}
        format_params = format_params or {}
        
        # Start timing
        total_start_time = time.time()
        
        # Start query logging
        query_id = self.logger.log_query_start(nlq, user_id, session_info)
        
        try:
            # Update pipeline statistics
            self.pipeline_stats['total_queries'] += 1
            
            logger.info(f"🔄 Processing query {query_id}: {nlq[:100]}...")
            
            # Step 1: Generate SQL from natural language
            logger.info("🧠 Generating SQL...")
            generation_start = time.time()
            
            generation_result = self.inference_engine.generate_sql(nlq, **generation_params)
            generation_time = time.time() - generation_start
            
            # Log SQL generation
            self.logger.log_sql_generation(query_id, generation_result)
            
            # Check if SQL generation was successful
            if not generation_result.get('validation', {}).get('is_valid', False):
                error_msg = f"Invalid SQL generated: {'; '.join(generation_result.get('validation', {}).get('errors', []))}"
                
                self.pipeline_stats['failed_queries'] += 1
                error_type = 'SQL_GENERATION_ERROR'
                self.pipeline_stats['error_breakdown'][error_type] = (
                    self.pipeline_stats['error_breakdown'].get(error_type, 0) + 1
                )
                
                total_time = time.time() - total_start_time
                self.logger.log_query_complete(query_id, total_time, False)
                
                return {
                    'success': False,
                    'error': error_msg,
                    'error_type': error_type,
                    'query_id': query_id,
                    'nlq': nlq,
                    'generation_result': generation_result,
                    'total_time': total_time,
                    'pipeline_stage': 'sql_generation'
                }
            
            generated_sql = generation_result['generated_sql']
            logger.info(f"✅ SQL generated: {generated_sql[:100]}...")
            
            # Step 2: Execute SQL against database
            logger.info("💾 Executing SQL...")
            execution_start = time.time()
            
            execution_result = self.database_executor.execute_query(
                generated_sql, 
                **execution_params
            )
            execution_time = time.time() - execution_start
            
            # Log database execution
            self.logger.log_database_execution(query_id, execution_result)
            
            # Check if execution was successful
            if not execution_result.get('success', False):
                error_msg = execution_result.get('error', 'Database execution failed')
                
                self.pipeline_stats['failed_queries'] += 1
                error_type = execution_result.get('error_type', 'DATABASE_ERROR')
                self.pipeline_stats['error_breakdown'][error_type] = (
                    self.pipeline_stats['error_breakdown'].get(error_type, 0) + 1
                )
                
                total_time = time.time() - total_start_time
                self.logger.log_query_complete(query_id, total_time, False)
                
                return {
                    'success': False,
                    'error': error_msg,
                    'error_type': error_type,
                    'query_id': query_id,
                    'nlq': nlq,
                    'generated_sql': generated_sql,
                    'generation_result': generation_result,
                    'execution_result': execution_result,
                    'total_time': total_time,
                    'pipeline_stage': 'database_execution'
                }
            
            rows_returned = execution_result.get('rows_returned', 0)
            logger.info(f"✅ SQL executed: {rows_returned} rows returned")
            
            # Step 3: Format results
            logger.info("🎨 Formatting results...")
            formatting_start = time.time()
            
            format_result = self.result_formatter.format_multiple(
                execution_result, 
                output_formats,
                **format_params
            )
            formatting_time = time.time() - formatting_start
            
            # Log result formatting
            self.logger.log_result_formatting(query_id, format_result)
            
            # Calculate total time
            total_time = time.time() - total_start_time
            
            # Update statistics
            self.pipeline_stats['successful_queries'] += 1
            self._update_timing_stats(total_time, generation_time, execution_time, formatting_time)
            
            # Log performance metrics
            self.logger.log_performance_metrics('pipeline', {
                'total_time': total_time,
                'generation_time': generation_time,
                'execution_time': execution_time,
                'formatting_time': formatting_time,
                'rows_returned': rows_returned
            }, query_id)
            
            # Complete query logging
            self.logger.log_query_complete(query_id, total_time, True, {
                'rows_returned': rows_returned,
                'formats': format_result.get('formats', {})
            })
            
            # Build final result
            final_result = {
                'success': True,
                'query_id': query_id,
                'nlq': nlq,
                'generated_sql': generated_sql,
                'results': format_result,
                'metadata': {
                    'total_time': total_time,
                    'generation_time': generation_time,
                    'execution_time': execution_time,
                    'formatting_time': formatting_time,
                    'rows_returned': rows_returned,
                    'output_formats': output_formats,
                    'truncated': execution_result.get('truncated', False)
                },
                'generation_details': generation_result,
                'execution_details': {
                    'query_id': execution_result.get('query_id'),
                    'execution_time': execution_result.get('execution_time'),
                    'security_check': execution_result.get('security_check', {})
                }
            }
            
            logger.info(f"🎉 Query {query_id} completed successfully in {total_time:.3f}s")
            return final_result
            
        except Exception as e:
            # Handle unexpected errors
            total_time = time.time() - total_start_time
            
            self.pipeline_stats['failed_queries'] += 1
            error_type = 'PIPELINE_ERROR'
            self.pipeline_stats['error_breakdown'][error_type] = (
                self.pipeline_stats['error_breakdown'].get(error_type, 0) + 1
            )
            
            # Log error
            self.logger.log_error(e, {
                'component': 'inference_pipeline',
                'query_id': query_id,
                'nlq': nlq,
                'total_time': total_time
            }, query_id)
            
            self.logger.log_query_complete(query_id, total_time, False)
            
            logger.error(f"❌ Unexpected error in pipeline: {e}")
            
            return {
                'success': False,
                'error': f"Pipeline error: {str(e)}",
                'error_type': error_type,
                'query_id': query_id,
                'nlq': nlq,
                'total_time': total_time,
                'pipeline_stage': 'unknown'
            }
    
    def batch_process(self, 
                     queries: List[str],
                     output_formats: List[str] = None,
                     user_id: Optional[str] = None,
                     **process_params) -> Dict[str, Any]:
        """
        Process multiple queries in batch.
        
        Args:
            queries: List of natural language queries
            output_formats: List of desired output formats
            user_id: User identifier for logging
            **process_params: Additional parameters for process_query
            
        Returns:
            Dict with batch processing results
        """
        if not self.is_initialized:
            return {
                'success': False,
                'error': 'Pipeline not initialized. Call initialize() first.',
                'pipeline_ready': False
            }
        
        logger.info(f"🔄 Processing batch of {len(queries)} queries")
        batch_start_time = time.time()
        
        results = []
        successful_count = 0
        failed_count = 0
        
        for i, query in enumerate(queries):
            logger.info(f"  Processing query {i+1}/{len(queries)}")
            
            result = self.process_query(
                query,
                output_formats=output_formats,
                user_id=user_id,
                session_info={'batch_index': i, 'batch_size': len(queries)},
                **process_params
            )
            
            results.append(result)
            
            if result.get('success', False):
                successful_count += 1
            else:
                failed_count += 1
        
        batch_time = time.time() - batch_start_time
        
        batch_result = {
            'success': True,
            'batch_size': len(queries),
            'successful_queries': successful_count,
            'failed_queries': failed_count,
            'success_rate': successful_count / len(queries),
            'total_batch_time': batch_time,
            'avg_query_time': batch_time / len(queries),
            'results': results,
            'summary': {
                'queries_processed': len(queries),
                'total_rows_returned': sum(r.get('metadata', {}).get('rows_returned', 0) for r in results),
                'error_breakdown': {}
            }
        }
        
        # Analyze error breakdown
        for result in results:
            if not result.get('success', False):
                error_type = result.get('error_type', 'UNKNOWN')
                batch_result['summary']['error_breakdown'][error_type] = (
                    batch_result['summary']['error_breakdown'].get(error_type, 0) + 1
                )
        
        logger.info(f"✅ Batch processing completed: {successful_count}/{len(queries)} successful")
        return batch_result
    
    def _update_timing_stats(self, total_time: float, generation_time: float, 
                           execution_time: float, formatting_time: float):
        """Update timing statistics."""
        total_queries = self.pipeline_stats['total_queries']
        
        # Update averages using incremental calculation
        self.pipeline_stats['avg_total_time'] = (
            (self.pipeline_stats['avg_total_time'] * (total_queries - 1) + total_time) / total_queries
        )
        self.pipeline_stats['avg_generation_time'] = (
            (self.pipeline_stats['avg_generation_time'] * (total_queries - 1) + generation_time) / total_queries
        )
        self.pipeline_stats['avg_execution_time'] = (
            (self.pipeline_stats['avg_execution_time'] * (total_queries - 1) + execution_time) / total_queries
        )
        self.pipeline_stats['avg_formatting_time'] = (
            (self.pipeline_stats['avg_formatting_time'] * (total_queries - 1) + formatting_time) / total_queries
        )
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Get current pipeline status and health information.
        
        Returns:
            Dict with pipeline status
        """
        status = {
            'pipeline_ready': self.is_initialized,
            'model_loaded': self.model_loaded,
            'database_connected': self.database_connected,
            'components_status': {
                'inference_engine': {
                    'loaded': self.model_loaded,
                    'info': self.inference_engine.get_model_info() if self.model_loaded else {}
                },
                'database_executor': {
                    'connected': self.database_connected,
                    'stats': self.database_executor.get_execution_stats() if self.database_connected else {}
                },
                'result_formatter': {
                    'stats': self.result_formatter.get_formatting_stats()
                }
            },
            'pipeline_stats': self.pipeline_stats.copy(),
            'logger_stats': self.logger.get_session_stats()
        }
        
        # Add health check
        if self.database_connected:
            connection_test = self.database_executor.test_connection()
            status['database_health'] = connection_test
        
        return status
    
    def benchmark_pipeline(self, test_queries: List[str] = None) -> Dict[str, Any]:
        """
        Benchmark the complete pipeline performance.
        
        Args:
            test_queries: List of test queries (uses defaults if None)
            
        Returns:
            Dict with benchmark results
        """
        if not self.is_initialized:
            return {
                'success': False,
                'error': 'Pipeline not initialized. Call initialize() first.'
            }
        
        # Default test queries
        if test_queries is None:
            test_queries = [
                "How many patients do we have?",
                "Show me all male patients",
                "Find patients with diabetes",
                "What are the most common conditions?",
                "List all healthcare organizations"
            ]
        
        logger.info(f"⚡ Benchmarking pipeline with {len(test_queries)} queries")
        
        # Run benchmark
        benchmark_result = self.batch_process(
            test_queries,
            output_formats=['table', 'json'],
            user_id='benchmark_user'
        )
        
        # Add detailed analysis
        if benchmark_result.get('success', False):
            results = benchmark_result['results']
            
            # Analyze timing breakdown
            timing_analysis = {
                'avg_generation_time': sum(r.get('metadata', {}).get('generation_time', 0) for r in results) / len(results),
                'avg_execution_time': sum(r.get('metadata', {}).get('execution_time', 0) for r in results) / len(results),
                'avg_formatting_time': sum(r.get('metadata', {}).get('formatting_time', 0) for r in results) / len(results),
                'avg_total_time': sum(r.get('metadata', {}).get('total_time', 0) for r in results) / len(results)
            }
            
            benchmark_result['timing_analysis'] = timing_analysis
            benchmark_result['benchmark_timestamp'] = time.time()
        
        logger.info("✅ Pipeline benchmark completed")
        return benchmark_result
    
    def reset_stats(self):
        """Reset all pipeline statistics."""
        self.pipeline_stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'avg_total_time': 0.0,
            'avg_generation_time': 0.0,
            'avg_execution_time': 0.0,
            'avg_formatting_time': 0.0,
            'error_breakdown': {},
            'initialization_time': self.pipeline_stats.get('initialization_time')
        }
        
        # Reset component stats
        if hasattr(self.inference_engine, 'reset_stats'):
            self.inference_engine.reset_stats()
        if hasattr(self.database_executor, 'reset_stats'):
            self.database_executor.reset_stats()
        if hasattr(self.result_formatter, 'reset_stats'):
            self.result_formatter.reset_stats()
        
        logger.info("📊 Pipeline statistics reset")
    
    def close(self):
        """Close pipeline and cleanup resources."""
        logger.info("🔚 Closing inference pipeline")
        
        # Close database connections
        if self.database_executor:
            self.database_executor.close()
        
        # Close logger
        if self.logger:
            self.logger.close()
        
        self.is_initialized = False
        self.model_loaded = False
        self.database_connected = False
        
        logger.info("✅ Pipeline closed successfully")


# Convenience function for quick pipeline usage
def create_pipeline(config_path: str = "d:/projects/healthca/config/config.yaml",
                   model_path: Optional[str] = None,
                   auto_initialize: bool = True) -> InferencePipeline:
    """
    Create and optionally initialize an inference pipeline.
    
    Args:
        config_path: Path to configuration file
        model_path: Path to trained model
        auto_initialize: Whether to automatically initialize the pipeline
        
    Returns:
        InferencePipeline instance
    """
    pipeline = InferencePipeline(config_path, model_path, auto_connect=auto_initialize)
    return pipeline


# Example usage function
def example_usage():
    """Example of how to use the inference pipeline."""
    
    # Create and initialize pipeline
    pipeline = create_pipeline()
    
    if not pipeline.is_initialized:
        print("❌ Pipeline initialization failed")
        return
    
    # Process a single query
    result = pipeline.process_query(
        "How many patients do we have?",
        output_formats=['table', 'json']
    )
    
    if result['success']:
        print(f"✅ Query successful: {result['metadata']['rows_returned']} rows returned")
        print(f"⏱️ Total time: {result['metadata']['total_time']:.3f}s")
    else:
        print(f"❌ Query failed: {result['error']}")
    
    # Get pipeline status
    status = pipeline.get_pipeline_status()
    print(f"📊 Pipeline processed {status['pipeline_stats']['total_queries']} queries")
    
    # Close pipeline
    pipeline.close()


if __name__ == "__main__":
    example_usage()