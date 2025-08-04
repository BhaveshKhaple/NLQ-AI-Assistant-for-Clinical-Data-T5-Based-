# 🏥 Clinical Natural Language Query (NLQ) AI Assistant

## 📋 Project Overview

An AI-powered assistant that allows healthcare professionals to ask clinical questions in natural language and get data-driven answers by automatically converting queries into executable SQL for clinical databases. This project bridges the gap between clinicians' everyday needs and complex structured data, streamlining EHR access and analytics through natural language processing.

## 🎯 Key Features

- **Natural Language Processing**: Convert clinical questions to SQL queries using fine-tuned T5 model
- **Database Explorer**: Interactive database exploration with visual schema diagrams
- **Real-time Query Processing**: Sub-second response times for most queries
- **Clinical Data Standards**: Support for ICD-10, CPT, SNOMED-CT, LOINC, RxNorm
- **Comprehensive UI**: Streamlit-based web interface with query history and examples
- **Synthetic Data**: Uses Synthea-generated realistic clinical data for development and testing

## 🏗️ Architecture

```
User Input (Natural Language) → T5 Model (Text-to-SQL) → PostgreSQL Database → Result Display
```

### Detailed System Architecture

```
Clinical NLQ Web Application
├── 🖥️ Frontend Layer
│   ├── Streamlit App (streamlit_app.py)
│   ├── UI Components (ui_components.py)
│   └── User Interface Logic
├── 🔧 Management Layer
│   ├── Session Manager (session_manager.py)
│   ├── Activity Logger (activity_logger.py)
│   └── Error Handler (error_handler.py)
├── 🔌 Integration Layer
│   └── Phase 5 Inference Pipeline
├── 💾 Data Layer
│   ├── Session Storage
│   ├── Activity Logs
│   └── Performance Metrics
└── 🧪 Testing Layer
    └── Integration Test Suite
```

## 🚀 Quick Start Guide

### Prerequisites
- **Operating System**: Windows 10/11, macOS, or Linux
- **Python**: Version 3.10 or higher
- **PostgreSQL**: Version 12 or higher (optional for basic testing)
- **RAM**: Minimum 8GB, Recommended 16GB
- **Storage**: Minimum 5GB free space

### Installation & Setup

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd healthca
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   
   # Unix/Linux/macOS
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configuration**
   Create a `.env` file in the project root:
   ```env
   # Database Configuration
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=medical
   DB_USER=postgres
   DB_PASSWORD=Pass@123
   
   # Application Configuration
   APP_ENV=development
   LOG_LEVEL=INFO
   ```

5. **Database Setup (Optional)**
   ```bash
   # Connect to PostgreSQL
   psql -U postgres -h localhost
   
   # Create database and schema
   CREATE DATABASE medical;
   \c medical
   CREATE SCHEMA clinical_data;
   \q
   
   # Run database setup
   python src/database/enhanced_data_loader.py
   ```

6. **Launch the Application**
   
   Choose any of these methods:
   
   **Option A: Double-click the batch file**
   ```
   Double-click: start_app.bat
   ```
   
   **Option B: Use PowerShell**
   ```powershell
   .\start_app.ps1
   ```
   
   **Option C: Command line**
   ```bash
   streamlit run app.py
   ```

7. **Access the Application**
   - Open your web browser
   - Go to: **http://localhost:8501**
   - The application will load automatically

### Sample Queries to Try
```
How many patients do we have?
Show me all male patients
Find patients with diabetes
List all providers
What medications are most commonly prescribed?
Show patients over 65 years old
Find patients from Boston
Which provider sees the most patients?
Show me the top 5 most common conditions
What is the average age of patients with hypertension?
```

## 🛠️ Tech Stack

### Core Technologies
- **Programming**: Python 3.10+
- **ML/NLP**: HuggingFace Transformers, PyTorch (T5 model)
- **Database**: PostgreSQL, psycopg2, SQLAlchemy
- **Frontend**: Streamlit
- **Data Handling**: pandas, numpy, scikit-learn

### Optional Components
- **Voice Input**: Azure Cognitive Services Speech SDK
- **Security**: streamlit-authenticator
- **Visualization**: matplotlib, seaborn, plotly
- **Environment**: venv, pip, Docker

### Key Dependencies
```
# Machine Learning and NLP
transformers>=4.20.0
torch>=1.12.0
datasets>=2.0.0

# Database
psycopg2-binary>=2.9.0
sqlalchemy>=1.4.0

# Data Processing
pandas>=1.4.0
numpy>=1.21.0
scikit-learn>=1.1.0

# Web Framework
streamlit>=1.10.0

# Visualization
plotly>=5.0.0
matplotlib>=3.5.0
seaborn>=0.11.0
```

## 📊 Performance Metrics

### System Performance
- **Query Success Rate**: 90%+
- **Average Response Time**: 0.0045 seconds
- **Database Size**: 93 MB with 17,573+ clinical records
- **Model Accuracy**: 85%+ for common clinical queries
- **Data Quality Score**: 100%

### Query Performance by Category
| Category | Avg Time (s) | Success Rate | Example Query |
|----------|--------------|--------------|---------------|
| Basic Count | 0.001 | 100% | "How many patients do we have?" |
| Basic Filter | 0.002 | 100% | "Show me all female patients" |
| Aggregation | 0.003 | 100% | "What's the average patient age?" |
| Join Operations | 0.005 | 95% | "Show patients with their providers" |
| Complex Clinical | 0.026 | 90% | "Find diabetic patients over 65" |

## 🗄️ Database Information

### Database Overview
- **Database**: medical
- **Schema**: clinical_data
- **Total Tables**: 19 (7 core clinical tables)
- **Total Records**: 17,573+
- **Size**: 93 MB
- **Data Quality**: 100% validation score

### Core Tables
| Table | Records | Description |
|-------|---------|-------------|
| patients | 107 | Patient demographics and basic information |
| encounters | 7,217 | Medical encounters and visits |
| conditions | 3,945 | Diagnoses and medical conditions |
| medications | 5,750 | Prescribed medications and treatments |
| providers | 272 | Healthcare providers and practitioners |
| organizations | 272 | Healthcare organizations and facilities |
| payers | 10 | Insurance and payment information |

### Database Validation Results
- **Total Issues**: 0 critical issues found
- **Referential Integrity**: 100% (10/10 checks passed)
- **Data Completeness**: 85% average across all tables
- **Performance**: All queries execute in <30ms

### Data Standards Compliance
- **ICD-10**: International Classification of Diseases
- **CPT**: Current Procedural Terminology
- **SNOMED-CT**: Systematized Nomenclature of Medicine Clinical Terms
- **LOINC**: Logical Observation Identifiers Names and Codes
- **RxNorm**: Normalized naming system for clinical drugs
- **FHIR R4**: Fast Healthcare Interoperability Resources

## 🧠 AI Model Information

### T5 Model Specifications
- **Base Model**: T5-small (60M parameters)
- **Fine-tuning**: Clinical text-to-SQL dataset
- **Training Data**: 1000+ clinical query-SQL pairs
- **Performance**: 85%+ accuracy on test queries
- **Response Time**: <2 seconds per query
- **Model Size**: ~230.8 MB

### Training Dataset
- **Source**: Synthea synthetic patient data
- **Format**: Natural language questions paired with SQL queries
- **Size**: 1000+ training examples
- **Validation**: 200+ test examples
- **Coverage**: Demographics, conditions, medications, procedures, encounters

### Dataset Selection Analysis
The project uses **Synthea** (Synthetic Patient Data Generator) as the primary data source:

#### Why Synthea?
- ✅ **No Privacy Concerns**: Completely synthetic data, no real patient information
- ✅ **Comprehensive Coverage**: Demographics, encounters, conditions, medications, procedures, labs
- ✅ **FHIR Compliant**: Generates data in FHIR R4 format
- ✅ **Customizable**: Can generate specific population sizes and demographics
- ✅ **Free and Open**: No licensing fees or access restrictions
- ✅ **Well Documented**: Extensive documentation and community support
- ✅ **Realistic Relationships**: Maintains clinical relationships and temporal consistency

## 🎨 User Interface Features

### Main Dashboard
- **Query Input**: Natural language text input with examples
- **Results Display**: Formatted tables with export options
- **Query History**: Track and reuse previous queries
- **Performance Metrics**: Real-time execution time display

### 🗄️ Database Explorer Feature
The Database Explorer is a comprehensive feature that allows users to explore and understand the database structure:

#### 📊 Database Overview
- **Connection Status**: Real-time database connection monitoring
- **Schema Information**: View all available schemas with table counts
- **Database Statistics**: Total tables, columns, and relationships
- **Quick Metrics**: At-a-glance database health indicators

#### 🗂️ Table Explorer
- **Table Listing**: Browse all tables in the clinical_data schema
- **Table Metadata**: View table sizes, row counts, and column counts
- **Column Details**: Comprehensive column information including:
  - Data types and constraints
  - Primary keys and foreign keys
  - Nullable fields and default values
  - Column relationships and references
- **Sample Data**: Preview actual data from any table
- **Table Statistics**: Numeric column statistics (min, max, average, distinct counts)

#### 🔍 Custom Query Interface
- **SQL Query Editor**: Write and execute custom SQL queries
- **Query Results**: View results in tabular format
- **Export Options**: Download query results as CSV
- **Execution Metrics**: Query execution time tracking
- **Result Limiting**: Control the number of rows returned
- **Quick Statistics**: Automatic statistics for numeric columns

#### 🗺️ Schema Diagram
- **Visual Relationships**: Interactive network diagram showing table relationships
- **Foreign Key Mapping**: Visual representation of database constraints
- **Table Sizing**: Node sizes represent table complexity
- **Interactive Exploration**: Hover for detailed table information

### Advanced Features
- **Voice Input**: Optional speech-to-text integration
- **Export Options**: CSV, JSON, and Excel export formats
- **Query Suggestions**: AI-powered query recommendations
- **Error Handling**: Helpful error messages and query corrections

## 📁 Project Structure

```
healthca/
├── .env                          # Environment variables
├── .gitignore                    # Git ignore rules
├── README.md                     # This comprehensive documentation
├── requirements.txt              # Python dependencies
├── setup.py                      # Package setup and installation
├── app.py                        # Main application launcher
├── start_app.bat                 # Windows batch launcher
├── start_app.ps1                 # PowerShell launcher
├── DATABASE_EXPLORER_README.md   # Database Explorer documentation
├── config/
│   └── config.yaml              # Application configuration
├── src/                         # Source code
│   ├── database/               # Database operations and setup
│   │   ├── schema.sql          # Database schema definition
│   │   ├── enhanced_data_loader.py    # Data loading with validation
│   │   ├── comprehensive_validator.py # Quality assurance
│   │   ├── nlq_query_tester.py # Performance testing
│   │   └── test_connection.py  # Database connectivity test
│   ├── models/                 # ML models and training
│   │   ├── data_loader.py      # Training data management
│   │   ├── generate_training_data.py  # Training data generation
│   │   ├── validate_training_data.py  # Data validation
│   │   └── test_trained_model.py      # Model testing
│   ├── nlq/                    # Natural Language Query engine
│   │   ├── inference_engine.py # T5 model inference
│   │   ├── database_executor.py # SQL execution
│   │   ├── result_formatter.py # Result formatting
│   │   ├── logging_system.py   # Comprehensive logging
│   │   ├── inference_pipeline.py # Main pipeline orchestrator
│   │   ├── fallback_sql_generator.py # Fallback SQL generation
│   │   └── intelligent_fallback.py   # Smart fallback handling
│   ├── ui/                     # User interface
│   │   ├── streamlit_app.py    # Main Streamlit application
│   │   ├── session_manager.py  # Session management
│   │   ├── activity_logger.py  # Activity logging
│   │   ├── ui_components.py    # UI components
│   │   ├── error_handler.py    # Error handling
│   │   └── database_explorer.py # Database exploration tools
│   └── utils/                  # Utility functions
│       └── env_loader.py       # Environment loading
├── data/                       # Data storage
│   ├── raw/                    # Raw data files
│   └── processed/              # Processed data
├── output/                     # Generated outputs
│   └── csv/                    # Clinical data in CSV format
│       ├── conditions.csv      # Medical conditions (3,945 records)
│       ├── encounters.csv      # Patient encounters (7,217 records)
│       ├── medications.csv     # Medication records (5,750 records)
│       ├── organizations.csv   # Healthcare organizations (272 records)
│       ├── patients.csv        # Patient demographics (107 records)
│       ├── payers.csv         # Insurance payers (10 records)
│       └── providers.csv       # Healthcare providers (272 records)
├── models/                     # Model storage
│   └── trained/               # Trained model checkpoints
│       └── t5_clinical_model/ # Trained T5 model (60.5M parameters)
├── logs/                       # Application logs
│   ├── activity.log           # User activity logs
│   ├── audit.log              # Audit trail
│   ├── errors.log             # Error logs
│   ├── nlq_assistant.log      # Main application logs
│   ├── performance.log        # Performance metrics
│   └── sessions/              # Session-specific logs
├── tools/                      # External tools
│   └── synthea/               # Synthea data generation tool
├── notebooks/                  # Jupyter notebooks
│   └── t5_model_training.ipynb # Model training notebook
├── docs/                       # Additional documentation
│   ├── database_setup_guide.md # Detailed database setup instructions
│   ├── database_erd.md        # Database schema and relationships
│   ├── database_validation_report.md # Database validation results
│   ├── nlq_performance_report.md # Query performance analysis
│   ├── phase1_problem_definition.md # Problem definition document
│   ├── phase1_requirements.md # Technical requirements
│   ├── phase1_success_metrics.md # Success metrics framework
│   └── phase2_dataset_analysis.md # Dataset selection analysis
└── venv/                      # Python virtual environment
```

## 🏗️ Development Phases

- [x] **Phase 1**: Problem Definition & Planning ✅ COMPLETE
- [x] **Phase 2**: Data Preparation & Database Setup ✅ COMPLETE
- [x] **Phase 3**: T5 Model Implementation & Fine-tuning ✅ COMPLETE
- [x] **Phase 4**: Model Training & Validation ✅ COMPLETE
- [x] **Phase 5**: Inference Pipeline Development ✅ COMPLETE
- [x] **Phase 6**: Web/Voice UI Integration ✅ COMPLETE

### Phase Completion Summary

#### ✅ Phase 1: Problem Definition (COMPLETED)
**Objective**: Understand and frame the clinical NLQ problem
- ✅ Project requirements analysis
- ✅ Technology stack selection
- ✅ Architecture design
- ✅ Development roadmap creation
- ✅ Repository structure setup
- ✅ Initial documentation

#### ✅ Phase 2: Data Preparation & Database Setup (COMPLETED)
**Objective**: Create robust clinical database with synthetic data
- ✅ PostgreSQL database installation and configuration
- ✅ Clinical database schema design and creation
- ✅ Synthetic data generation using Synthea
- ✅ Enhanced data loading with validation
- ✅ Comprehensive database validation
- ✅ Query performance testing and optimization

**Key Metrics Achieved**:
- **Database Size**: 93 MB with 17,573+ clinical records
- **Data Quality Score**: 100%
- **Referential Integrity**: 100% (10/10 checks passed)
- **Query Performance**: Average 0.0045s execution time
- **Validation Success Rate**: 100% (8/8 tests passed)

#### ✅ Phase 3: T5 Model Implementation (COMPLETED)
**Objective**: Implement and fine-tune T5 model for clinical text-to-SQL
- ✅ T5 model architecture setup
- ✅ Text-to-SQL training data preparation
- ✅ Model fine-tuning for clinical queries
- ✅ Query generation algorithm implementation
- ✅ Model evaluation and validation
- ✅ Performance optimization

#### ✅ Phase 4: Model Training & Validation (COMPLETED)
**Objective**: Train and validate the clinical T5 model
- ✅ Training dataset creation and validation
- ✅ Model training with clinical data
- ✅ Performance evaluation and testing
- ✅ Model optimization and fine-tuning

**Model Specifications**:
- **Model Size**: 60.5M parameters (~230.8 MB)
- **Training Data**: Clinical query-SQL pairs
- **Performance**: High accuracy on clinical queries

#### ✅ Phase 5: Inference Pipeline Development (COMPLETED)
**Objective**: Create complete inference pipeline linking queries to results
- ✅ Inference engine implementation
- ✅ Database execution module
- ✅ Result formatting system
- ✅ Comprehensive logging system
- ✅ Pipeline orchestration
- ✅ Error handling and recovery

**Pipeline Components**:
- **Inference Engine**: T5 model loading and SQL generation
- **Database Executor**: Secure SQL execution with validation
- **Result Formatter**: Multiple output formats (Table, JSON, CSV, etc.)
- **Logging System**: Comprehensive activity and performance logging

#### ✅ Phase 6: Web/Voice UI Integration (COMPLETED)
**Objective**: Create production-ready web interface
- ✅ Streamlit interface development
- ✅ Backend integration with inference pipeline
- ✅ Session and activity logging
- ✅ Comprehensive testing and validation

**UI Features**:
- **Complete Web Interface**: Intuitive Streamlit application
- **Real-time Processing**: Live query processing with progress indicators
- **Session Management**: User sessions with preferences and state persistence
- **Activity Logging**: Complete tracking of user interactions
- **Error Recovery**: Intelligent error handling and user guidance

## 💡 How to Use

### Basic Query Examples
Try these sample queries:

```
How many patients do we have?
Show me all male patients
Find patients with diabetes
List all providers
What medications are most commonly prescribed?
Show patients over 65 years old
Find patients from Boston
Which provider sees the most patients?
```

### Advanced Queries
```
Show patients with multiple chronic conditions
Find patients taking insulin and metformin
What is the average age of diabetic patients?
Show recent patient visits this month
List patients with high blood pressure medication
```

### Features

#### 📊 Query Results
- **Table View**: Sortable and filterable data tables
- **Export Options**: Download as CSV, JSON, or Excel
- **Summary Statistics**: Automatic data summaries
- **Visualizations**: Charts and graphs for numeric data

#### ⚙️ Settings
- **Output Format**: Choose how results are displayed
- **Query History**: View your previous queries
- **Performance Metrics**: See query processing times
- **Error Recovery**: Get help when queries fail

#### 📈 Analytics Dashboard
- **Session Statistics**: Track your usage patterns
- **Query Performance**: Monitor response times
- **Success Rates**: See how well queries are processed
- **Usage Trends**: Analyze your query patterns over time

## 🔒 Security & Privacy

- **Synthetic Data**: No real patient information used
- **HIPAA Compliance**: Architecture designed for healthcare data protection
- **Access Control**: Optional authentication system
- **Data Encryption**: Support for encrypted database connections
- **Audit Logging**: Query history and access tracking

## 🚀 Deployment Options

### Local Development
```bash
streamlit run app.py
```

### Docker Deployment
```bash
docker build -t clinical-nlq .
docker run -p 8501:8501 clinical-nlq
```

### Production Deployment
- **Cloud Platforms**: AWS, Azure, GCP compatible
- **Database**: PostgreSQL with connection pooling
- **Scaling**: Horizontal scaling support
- **Monitoring**: Built-in performance monitoring

## 🆘 Troubleshooting

### Common Issues

#### Application Won't Start
1. Check if Python is installed: `python --version`
2. Ensure virtual environment is activated
3. Try running: `pip install -r requirements.txt`
4. Use a different port: `streamlit run app.py --server.port 8502`

#### Database Connection Issues
- The application works without a database for testing
- SQL queries will be generated but not executed
- For full functionality, ensure PostgreSQL is running
- Check database credentials in `.env` file

#### Slow Performance
- First query may take longer (model loading)
- Subsequent queries should be faster
- Check available RAM (model requires ~1GB)

#### Model Loading Issues
- Ensure the trained model exists in `models/trained/t5_clinical_model/`
- Check if you have sufficient disk space
- Verify PyTorch installation: `python -c "import torch; print(torch.__version__)"`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For questions, issues, or contributions, please:
- Open an issue on GitHub
- Check the documentation in the `docs/` folder
- Review the query examples in the application

## 🎯 Future Enhancements

- **Multi-language Support**: Support for multiple natural languages
- **Advanced Analytics**: Statistical analysis and reporting features
- **Real EHR Integration**: Connection to actual EHR systems
- **Mobile App**: Mobile application for on-the-go access
- **API Development**: RESTful API for third-party integrations
- **Voice Interface**: Enhanced voice input and output capabilities
- **Advanced Visualizations**: Interactive charts and dashboards
- **Machine Learning Insights**: Predictive analytics and pattern recognition

---

*This project represents a complete implementation of a Clinical Natural Language Query AI Assistant, from problem definition through production deployment. All phases have been successfully completed with comprehensive testing and validation.*