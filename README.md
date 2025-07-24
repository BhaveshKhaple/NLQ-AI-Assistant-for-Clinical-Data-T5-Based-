# Clinical Natural Language Query (NLQ) AI Assistant

## Project Overview
An AI-powered assistant that allows users to ask clinical questions in natural language and get data-driven answers by automatically converting queries into executable SQL for a clinical database.

## Main Goal
Bridge clinicians' everyday needs with complex structured data, streamlining EHR access and analytics through natural language processing.

## Tech Stack
- **Programming**: Python 3.10+
- **ML/NLP**: HuggingFace Transformers, PyTorch (T5 model)
- **Data Handling**: pandas, numpy, scikit-learn
- **Database**: PostgreSQL, psycopg2, SQLAlchemy
- **Frontend**: Streamlit
- **Voice Input**: Azure Cognitive Services Speech SDK (Optional)
- **Security**: streamlit-authenticator (Optional)
- **Visualization**: matplotlib, seaborn
- **Environment**: venv, pip, Docker

## Architecture
```
User Input (Text/Voice) → T5 Model (Text-to-SQL) → PostgreSQL Database → Result Display
```

## Development Phases
- [x] **Phase 1**: Understand & Frame the Problem
- [ ] **Phase 2**: Data Preparation & Database Setup
- [ ] **Phase 3**: T5 Model Implementation & Fine-tuning
- [ ] **Phase 4**: Frontend Development
- [ ] **Phase 5**: Integration & Testing
- [ ] **Phase 6**: Deployment & Production

## Project Structure
```
healthca/
├── docs/                    # Documentation and requirements
├── src/                     # Source code
│   ├── models/             # ML models and training scripts
│   ├── database/           # Database schemas and operations
│   ├── nlq/                # Natural language query processing
│   └── ui/                 # Streamlit frontend
├── data/                   # Sample data and schemas
├── tests/                  # Unit and integration tests
├── config/                 # Configuration files
└── deployment/             # Docker and deployment scripts
```

## Getting Started
1. Set up Python virtual environment
2. Install dependencies from requirements.txt
3. Configure database connection
4. Run initial setup scripts
5. Launch Streamlit application

## Contributing
Please refer to the development phases and documentation in the `docs/` directory.