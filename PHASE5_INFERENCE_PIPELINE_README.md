# Phase 5: Inference Pipeline Development

## 🎯 Overview

This document describes the complete implementation of Phase 5: Inference Pipeline Development for the Clinical NLQ AI Assistant. The inference pipeline links user queries to results through the trained T5 model and database, providing a complete end-to-end solution for natural language to SQL conversion and execution.

## 🏗️ Architecture

The inference pipeline consists of four main components:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                  │    │                 │    │                 │
│ Inference       │───▶│ Database         │───▶│ Result          │───▶│ Logging         │
│ Engine          │    │ Executor         │    │ Formatter       │    │ System          │
│                 │    │                  │    │                 │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘    └─────────────────┘
│                                                                                        │
└────────────────────────────── Inference Pipeline ──────────────────────────────────┘
```

## 📁 File Structure

```
src/nlq/
├── __init__.py                 # Module initialization
├── inference_engine.py         # T5 model loading and SQL generation
├── database_executor.py        # Secure SQL execution
├── result_formatter.py         # Multi-format result formatting
├── logging_system.py          # Comprehensive logging
└── inference_pipeline.py      # Main orchestrator

# Test and example files
├── test_inference_pipeline.py  # Comprehensive testing
├── example_inference_usage.py  # Usage examples
└── PHASE5_INFERENCE_PIPELINE_README.md  # This documentation
```

## 🔧 Components

### 1. Inference Engine (`inference_engine.py`)

**Purpose**: Handles T5 model loading, tokenization, and SQL generation from natural language queries.

**Key Features**:
- Automatic model discovery from multiple possible paths
- Schema context injection for better SQL generation
- Multiple generation strategies (greedy, beam search, sampling)
- SQL validation and quality checks
- Performance monitoring and statistics
- Batch processing support

**Usage**:
```python
from src.nlq.inference_engine import ClinicalInferenceEngine

engine = ClinicalInferenceEngine()
engine.load_model()

result = engine.generate_sql("How many patients do we have?")
print(result['generated_sql'])
```

### 2. Database Executor (`database_executor.py`)

**Purpose**: Securely executes generated SQL queries against PostgreSQL database with comprehensive error handling.

**Key Features**:
- Security validation (SQL injection prevention)
- Connection pooling and management
- Query timeout and resource limits
- Comprehensive error handling
- Performance monitoring
- Dry-run capability for query validation

**Security Features**:
- Whitelist-based operation filtering (only SELECT and WITH allowed)
- SQL injection pattern detection
- Schema compliance checking
- Resource exhaustion prevention

**Usage**:
```python
from src.nlq.database_executor import DatabaseExecutor

executor = DatabaseExecutor()
executor.connect()

result = executor.execute_query("SELECT COUNT(*) FROM clinical_data.patients")
print(f"Rows returned: {result['rows_returned']}")
```

### 3. Result Formatter (`result_formatter.py`)

**Purpose**: Formats query results into various output formats for different interfaces.

**Supported Formats**:
- **Table**: Structured table format with pagination
- **JSON**: JSON format with metadata
- **CSV**: Comma-separated values with customizable delimiters
- **DataFrame**: Pandas DataFrame with analysis
- **Streamlit**: Optimized format for Streamlit UI
- **Summary**: Statistical summary and analysis

**Usage**:
```python
from src.nlq.result_formatter import ResultFormatter

formatter = ResultFormatter()

# Format in multiple formats
result = formatter.format_multiple(
    query_result, 
    formats=['table', 'json', 'csv']
)
```

### 4. Logging System (`logging_system.py`)

**Purpose**: Comprehensive logging for debugging, auditing, and monitoring the inference pipeline.

**Log Types**:
- **Main Log**: General application events
- **Audit Log**: Security and compliance events (JSON format)
- **Performance Log**: Performance metrics and timing
- **Error Log**: Detailed error information with stack traces

**Features**:
- Structured JSON logging for audit trail
- Automatic log rotation
- Session tracking
- Performance metrics collection
- Security event logging

### 5. Inference Pipeline (`inference_pipeline.py`)

**Purpose**: Main orchestrator that coordinates all components to provide a complete inference solution.

**Key Features**:
- Complete pipeline orchestration
- Error handling and recovery
- Performance monitoring
- Batch processing
- Health checks and status monitoring
- Comprehensive statistics

## 🚀 Quick Start

### 1. Basic Usage

```python
from src.nlq.inference_pipeline import create_pipeline

# Create and initialize pipeline
pipeline = create_pipeline()

# Process a query
result = pipeline.process_query(
    "How many patients do we have?",
    output_formats=['table', 'json']
)

if result['success']:
    print(f"SQL: {result['generated_sql']}")
    print(f"Rows: {result['metadata']['rows_returned']}")
    print(f"Time: {result['metadata']['total_time']:.3f}s")
else:
    print(f"Error: {result['error']}")

# Close pipeline
pipeline.close()
```

### 2. Advanced Usage

```python
# Custom parameters
result = pipeline.process_query(
    nlq="Find elderly patients with diabetes",
    output_formats=['table', 'json', 'summary'],
    user_id='doctor_smith',
    generation_params={
        'num_beams': 8,
        'temperature': 0.7,
        'include_schema_context': True
    },
    execution_params={
        'timeout': 60,
        'max_rows': 1000
    }
)
```

### 3. Batch Processing

```python
queries = [
    "How many male patients?",
    "How many female patients?",
    "What's the average age?"
]

batch_result = pipeline.batch_process(
    queries,
    output_formats=['table'],
    user_id='analyst'
)

print(f"Success rate: {batch_result['success_rate']:.1%}")
```

## 🧪 Testing

### Run Comprehensive Tests

```bash
python test_inference_pipeline.py
```

This will run:
- Pipeline initialization tests
- Single query processing tests
- Batch processing tests
- Error handling tests
- Format testing
- Performance benchmarks

### Run Simple Examples

```bash
python example_inference_usage.py
```

## 📊 Configuration

The pipeline uses `config/config.yaml` for configuration:

```yaml
# Model Configuration
model:
  max_source_length: 512
  max_target_length: 512
  device: "auto"
  confidence_threshold: 0.7

# Database Configuration
database:
  host: "localhost"
  port: 5432
  name: "clinical_nlq"
  username: "nlq_user"
  schema: "clinical_data"

# Performance Configuration
performance:
  query_timeout: 30
  max_export_rows: 10000
  cache_results: true

# Logging Configuration
logging:
  level: "INFO"
  file: "./logs/nlq_assistant.log"
  audit_file: "./logs/audit.log"
```

## 🔒 Security Features

### SQL Injection Prevention
- Whitelist-based operation filtering
- Pattern detection for dangerous SQL
- Parameter validation
- Schema compliance checking

### Audit Trail
- All queries logged with user information
- Security events tracked
- Performance metrics recorded
- Error details captured

### Resource Protection
- Query timeouts
- Result size limits
- Connection pooling
- Memory usage monitoring

## 📈 Performance Monitoring

### Metrics Tracked
- Query processing times (generation, execution, formatting)
- Success/failure rates
- Resource usage
- Error patterns
- User activity

### Statistics Available
```python
status = pipeline.get_pipeline_status()
stats = status['pipeline_stats']

print(f"Total queries: {stats['total_queries']}")
print(f"Success rate: {stats['successful_queries']}/{stats['total_queries']}")
print(f"Average time: {stats['avg_total_time']:.3f}s")
```

## 🐛 Error Handling

The pipeline provides comprehensive error handling:

### Error Types
- `SQL_GENERATION_ERROR`: T5 model failed to generate valid SQL
- `SECURITY_VIOLATION`: Query failed security validation
- `DATABASE_ERROR`: Database connection or execution error
- `TIMEOUT_ERROR`: Query exceeded time limit
- `SQL_SYNTAX_ERROR`: Generated SQL has syntax errors
- `PIPELINE_ERROR`: Unexpected pipeline error

### Error Information
Each error includes:
- Error type and message
- Pipeline stage where error occurred
- Query ID for tracking
- Detailed context information
- Suggested remediation (where applicable)

## 📝 Logging

### Log Files Created
- `logs/nlq_assistant.log`: Main application log
- `logs/audit.log`: Audit trail (JSON format)
- `logs/performance.log`: Performance metrics
- `logs/errors.log`: Detailed error information

### Log Rotation
- Automatic rotation when files exceed 10MB
- Keeps 5 backup files
- Configurable retention period

## 🔧 Troubleshooting

### Common Issues

1. **Model Not Found**
   - Check model paths in configuration
   - Ensure model files exist and are accessible
   - Verify model format compatibility

2. **Database Connection Failed**
   - Check database configuration
   - Verify DB_PASSWORD environment variable
   - Ensure PostgreSQL is running
   - Check network connectivity

3. **SQL Generation Issues**
   - Review training data quality
   - Check model performance metrics
   - Consider retraining with better data

4. **Performance Issues**
   - Monitor query complexity
   - Check database indexes
   - Review resource limits
   - Consider connection pooling adjustments

### Debug Mode

Enable debug logging:
```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

## 🚀 Deployment Considerations

### Production Checklist
- [ ] Set secure database passwords
- [ ] Configure appropriate timeouts
- [ ] Set up log rotation
- [ ] Monitor resource usage
- [ ] Implement backup strategies
- [ ] Set up alerting
- [ ] Configure SSL/TLS
- [ ] Review security settings

### Scaling Considerations
- Connection pooling for multiple users
- Caching for frequently used queries
- Load balancing for high availability
- Monitoring and alerting systems

## 📚 API Reference

### InferencePipeline Class

#### Methods

- `initialize()`: Initialize the complete pipeline
- `process_query(nlq, **kwargs)`: Process a single query
- `batch_process(queries, **kwargs)`: Process multiple queries
- `get_pipeline_status()`: Get current status and statistics
- `benchmark_pipeline()`: Run performance benchmark
- `reset_stats()`: Reset all statistics
- `close()`: Close pipeline and cleanup resources

#### Parameters

**process_query() parameters**:
- `nlq`: Natural language query (required)
- `output_formats`: List of desired formats ['table', 'json', 'csv', etc.]
- `user_id`: User identifier for logging
- `session_info`: Additional session information
- `generation_params`: Parameters for SQL generation
- `execution_params`: Parameters for database execution
- `format_params`: Parameters for result formatting

## 🎯 Success Criteria Met

✅ **Inference Function Created**: Complete T5 model loading and SQL generation  
✅ **Execution Module Implemented**: Secure SQL execution with comprehensive error handling  
✅ **Result Formatting**: Multiple output formats (table, JSON, CSV, DataFrame, Streamlit, summary)  
✅ **Comprehensive Logging**: All activities logged for debugging, auditing, and monitoring  
✅ **Security Features**: SQL injection prevention, audit trails, resource protection  
✅ **Performance Monitoring**: Detailed metrics and statistics collection  
✅ **Error Handling**: Comprehensive error handling with detailed context  
✅ **Testing Suite**: Complete test coverage with examples  

## 🔮 Future Enhancements

- **Caching**: Implement query result caching
- **Voice Input**: Add voice-to-text capabilities
- **Real-time Monitoring**: Dashboard for real-time monitoring
- **Advanced Analytics**: Query pattern analysis and optimization
- **Multi-language Support**: Support for multiple languages
- **API Endpoints**: REST API for external integrations

---

**Status**: ✅ **COMPLETE - PHASE 5 SUCCESSFULLY IMPLEMENTED**

The inference pipeline is fully functional and ready for integration with the Streamlit UI and production deployment.