# Phase 1: Technical Requirements Document

## System Architecture Overview

### High-Level Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌──────────────────┐
│   User Input    │    │   NLQ Processor  │    │  SQL Generator  │    │   PostgreSQL     │
│  (Text/Voice)   │───▶│   (T5 Model)     │───▶│   & Validator   │───▶│    Database      │
└─────────────────┘    └──────────────────┘    └─────────────────┘    └──────────────────┘
                                │                        │                        │
                                ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌──────────────────┐
│   Streamlit     │    │   Query History  │    │   Result Cache  │    │   Audit Logging  │
│   Frontend      │◀───│   & Analytics    │    │   & Storage     │    │   & Monitoring   │
└─────────────────┘    └──────────────────┘    └─────────────────┘    └──────────────────┘
```

### Component Breakdown

1. **Natural Language Processor**
   - T5 transformer model for text-to-SQL conversion
   - Clinical terminology preprocessor
   - Query intent classification
   - Confidence scoring mechanism

2. **SQL Generation & Validation**
   - Template-based SQL generation
   - Query syntax validation
   - Performance optimization
   - Security injection prevention

3. **Database Layer**
   - PostgreSQL connection management
   - Query execution engine
   - Result formatting and pagination
   - Transaction management

4. **User Interface**
   - Streamlit web application
   - Voice input integration (optional)
   - Result visualization
   - Query history management

## Detailed Technical Requirements

### 1. Natural Language Processing Requirements

#### Input Processing
- **Text Input**: Support for clinical questions up to 500 characters
- **Voice Input**: Integration with Azure Speech Services (optional)
- **Language Support**: English (primary), with extensibility for other languages
- **Clinical Terminology**: Support for medical abbreviations, drug names, procedure codes

#### NLQ Capabilities
```python
# Example supported query types
SUPPORTED_QUERY_TYPES = {
    "patient_demographics": "Show me male patients over 65",
    "diagnosis_queries": "Patients with diabetes and hypertension",
    "temporal_queries": "Admissions in the last 30 days",
    "medication_queries": "Patients on insulin therapy",
    "lab_result_queries": "High glucose levels in diabetic patients",
    "procedure_queries": "Cardiac catheterizations this year",
    "statistical_queries": "Average length of stay for heart surgery",
    "comparative_queries": "Compare readmission rates by department"
}
```

#### Model Specifications
- **Base Model**: T5-base or T5-large from HuggingFace
- **Fine-tuning Data**: Clinical text-to-SQL pairs (minimum 10,000 examples)
- **Inference Time**: < 2 seconds for query conversion
- **Accuracy Target**: >= 85% correct SQL generation
- **Confidence Scoring**: Probabilistic confidence for each generated query

### 2. Database Requirements

#### PostgreSQL Schema Design
```sql
-- Core clinical tables structure
CREATE SCHEMA clinical_data;

-- Patients table
CREATE TABLE clinical_data.patients (
    patient_id UUID PRIMARY KEY,
    mrn VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    date_of_birth DATE NOT NULL,
    gender VARCHAR(10),
    race VARCHAR(50),
    ethnicity VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Encounters table
CREATE TABLE clinical_data.encounters (
    encounter_id UUID PRIMARY KEY,
    patient_id UUID REFERENCES clinical_data.patients(patient_id),
    encounter_type VARCHAR(50) NOT NULL,
    admission_date TIMESTAMP,
    discharge_date TIMESTAMP,
    department VARCHAR(100),
    attending_physician VARCHAR(100),
    primary_diagnosis_code VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Diagnoses table
CREATE TABLE clinical_data.diagnoses (
    diagnosis_id UUID PRIMARY KEY,
    patient_id UUID REFERENCES clinical_data.patients(patient_id),
    encounter_id UUID REFERENCES clinical_data.encounters(encounter_id),
    icd10_code VARCHAR(10) NOT NULL,
    diagnosis_description TEXT,
    diagnosis_date DATE NOT NULL,
    diagnosis_type VARCHAR(20), -- primary, secondary, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Medications table
CREATE TABLE clinical_data.medications (
    medication_id UUID PRIMARY KEY,
    patient_id UUID REFERENCES clinical_data.patients(patient_id),
    encounter_id UUID REFERENCES clinical_data.encounters(encounter_id),
    medication_name VARCHAR(200) NOT NULL,
    dosage VARCHAR(100),
    route VARCHAR(50),
    frequency VARCHAR(100),
    start_date DATE,
    end_date DATE,
    prescribing_physician VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Lab results table
CREATE TABLE clinical_data.lab_results (
    lab_result_id UUID PRIMARY KEY,
    patient_id UUID REFERENCES clinical_data.patients(patient_id),
    encounter_id UUID REFERENCES clinical_data.encounters(encounter_id),
    test_name VARCHAR(200) NOT NULL,
    test_code VARCHAR(20),
    result_value DECIMAL(10,3),
    result_unit VARCHAR(20),
    reference_range VARCHAR(100),
    abnormal_flag VARCHAR(10),
    test_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Database Performance Requirements
- **Query Response Time**: < 5 seconds for complex joins
- **Concurrent Connections**: Support 100+ simultaneous connections
- **Data Volume**: Optimized for 1M+ patient records
- **Indexing Strategy**: Comprehensive indexing on frequently queried columns
- **Backup & Recovery**: Daily automated backups with point-in-time recovery

### 3. Machine Learning Model Requirements

#### T5 Model Configuration
```python
# Model configuration
MODEL_CONFIG = {
    "model_name": "t5-base",  # or t5-large for better performance
    "max_source_length": 512,
    "max_target_length": 512,
    "learning_rate": 1e-4,
    "batch_size": 8,
    "num_epochs": 10,
    "warmup_steps": 1000,
    "weight_decay": 0.01,
    "gradient_accumulation_steps": 4
}

# Training data format
TRAINING_EXAMPLE = {
    "input_text": "Show me patients with diabetes admitted last month",
    "target_sql": """SELECT p.patient_id, p.first_name, p.last_name, e.admission_date
                     FROM clinical_data.patients p
                     JOIN clinical_data.encounters e ON p.patient_id = e.patient_id
                     JOIN clinical_data.diagnoses d ON p.patient_id = d.patient_id
                     WHERE d.icd10_code LIKE 'E11%'
                     AND e.admission_date >= CURRENT_DATE - INTERVAL '1 month'
                     AND e.admission_date < CURRENT_DATE"""
}
```

#### Model Training Pipeline
1. **Data Preparation**: Clean and preprocess clinical text-SQL pairs
2. **Tokenization**: Use T5 tokenizer with clinical vocabulary expansion
3. **Fine-tuning**: Domain-specific training on clinical data
4. **Validation**: Cross-validation with held-out clinical datasets
5. **Evaluation**: BLEU score, exact match, execution accuracy metrics

### 4. Frontend Requirements (Streamlit)

#### User Interface Components
```python
# Main interface components
UI_COMPONENTS = {
    "query_input": {
        "type": "text_area",
        "placeholder": "Enter your clinical question in natural language...",
        "max_chars": 500,
        "height": 100
    },
    "voice_input": {
        "type": "audio_recorder",
        "enabled": False,  # Optional feature
        "format": "wav",
        "sample_rate": 16000
    },
    "results_display": {
        "type": "dataframe",
        "pagination": True,
        "export_formats": ["CSV", "Excel", "PDF"],
        "max_rows_per_page": 50
    },
    "query_history": {
        "type": "selectbox",
        "save_favorites": True,
        "max_history": 100
    },
    "sql_viewer": {
        "type": "code_editor",
        "language": "sql",
        "read_only": True,
        "syntax_highlighting": True
    }
}
```

#### User Experience Requirements
- **Response Time**: Total page load time < 3 seconds
- **Mobile Responsive**: Optimized for tablets and mobile devices
- **Accessibility**: WCAG 2.1 AA compliance
- **Error Handling**: Clear, actionable error messages
- **Help System**: Built-in tutorials and documentation

### 5. Security & Privacy Requirements

#### HIPAA Compliance
```python
# Security configuration
SECURITY_CONFIG = {
    "encryption": {
        "data_at_rest": "AES-256",
        "data_in_transit": "TLS 1.3",
        "database_encryption": "PostgreSQL native encryption"
    },
    "authentication": {
        "method": "multi_factor",
        "session_timeout": 30,  # minutes
        "password_policy": "strong_passwords_required",
        "failed_attempts_lockout": 5
    },
    "authorization": {
        "role_based_access": True,
        "fine_grained_permissions": True,
        "audit_all_queries": True
    },
    "data_handling": {
        "phi_detection": True,
        "automatic_deidentification": True,
        "query_result_filtering": True
    }
}
```

#### Audit & Logging Requirements
- **Query Logging**: All queries logged with user, timestamp, and results
- **Access Logging**: All system access attempts logged
- **Data Access Tracking**: Detailed logs of data accessed and exported
- **Error Logging**: Comprehensive error tracking and alerting
- **Compliance Reporting**: Automated HIPAA compliance reports

### 6. Performance & Scalability Requirements

#### System Performance Targets
```python
PERFORMANCE_TARGETS = {
    "query_processing": {
        "nlp_conversion": "< 2 seconds",
        "sql_execution": "< 5 seconds",
        "result_rendering": "< 1 second",
        "total_response": "< 10 seconds"
    },
    "concurrent_users": {
        "supported_users": 50,
        "peak_load_handling": 100,
        "response_degradation": "< 20% at peak"
    },
    "data_handling": {
        "max_result_rows": 10000,
        "pagination_size": 50,
        "export_timeout": 300  # seconds
    }
}
```

#### Scalability Architecture
- **Horizontal Scaling**: Load balancer with multiple app instances
- **Database Scaling**: Read replicas for query distribution
- **Caching Layer**: Redis for query result caching
- **CDN Integration**: Static asset delivery optimization

### 7. Development & Deployment Requirements

#### Development Environment
```python
# Required Python packages
REQUIREMENTS = {
    "core": [
        "python>=3.10",
        "transformers>=4.20.0",
        "torch>=1.12.0",
        "datasets>=2.0.0",
        "tokenizers>=0.12.0"
    ],
    "database": [
        "psycopg2-binary>=2.9.0",
        "sqlalchemy>=1.4.0",
        "alembic>=1.8.0"
    ],
    "web": [
        "streamlit>=1.10.0",
        "streamlit-authenticator>=0.2.0",
        "plotly>=5.0.0",
        "pandas>=1.4.0"
    ],
    "ml": [
        "scikit-learn>=1.1.0",
        "numpy>=1.21.0",
        "scipy>=1.8.0"
    ],
    "optional": [
        "azure-cognitiveservices-speech>=1.22.0",
        "redis>=4.3.0",
        "celery>=5.2.0"
    ]
}
```

#### Deployment Requirements
- **Containerization**: Docker containers for all services
- **Orchestration**: Docker Compose for development, Kubernetes for production
- **CI/CD Pipeline**: Automated testing and deployment
- **Monitoring**: Comprehensive application and infrastructure monitoring
- **Backup Strategy**: Automated backups with disaster recovery procedures

## Testing Strategy

### Unit Testing
- **Model Testing**: T5 model conversion accuracy tests
- **Database Testing**: SQL generation and execution tests
- **UI Testing**: Streamlit component functionality tests
- **Security Testing**: Authentication and authorization tests

### Integration Testing
- **End-to-End**: Complete user workflow testing
- **Performance Testing**: Load testing with concurrent users
- **Security Testing**: Penetration testing and vulnerability assessment
- **Clinical Validation**: Domain expert validation of query results

### Quality Assurance
- **Code Coverage**: Minimum 80% test coverage
- **Static Analysis**: Automated code quality checks
- **Security Scanning**: Regular dependency vulnerability scans
- **Clinical Review**: Medical professional review of system outputs

## Implementation Timeline

### Phase 1 Deliverables (Current)
- [x] Problem definition document
- [x] Technical requirements specification
- [x] Project structure setup
- [ ] Success metrics definition
- [ ] Risk assessment completion

### Success Criteria for Phase 1
1. **Documentation Complete**: All Phase 1 documents reviewed and approved
2. **Requirements Validated**: Technical requirements confirmed with stakeholders
3. **Architecture Approved**: System architecture design validated
4. **Metrics Defined**: Clear success metrics established
5. **Risks Identified**: Comprehensive risk assessment completed

---
*Document Status: Draft v1.0*  
*Last Updated: [Current Date]*  
*Phase: 1 - Requirements Definition*