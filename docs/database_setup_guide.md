# Clinical Database Setup Guide

*Complete guide for setting up the clinical database for NLQ development*

## Overview

This guide provides step-by-step instructions for setting up a PostgreSQL clinical database with synthetic patient data for Natural Language Query (NLQ) development. The database contains realistic clinical data generated using Synthea and optimized for machine learning applications.

## Prerequisites

### System Requirements
- **Operating System**: Windows 10/11, macOS, or Linux
- **RAM**: Minimum 8GB, Recommended 16GB
- **Storage**: Minimum 5GB free space
- **Python**: Version 3.10 or higher
- **PostgreSQL**: Version 12 or higher

### Required Software
1. **PostgreSQL Database Server**
   - Download from: https://www.postgresql.org/download/
   - Ensure PostgreSQL service is running
   - Default port: 5432

2. **Python Environment**
   - Python 3.10+
   - pip package manager
   - Virtual environment support

## Installation Steps

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd healthca
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Database Connection

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

**Important**: Update the database credentials to match your PostgreSQL installation.

### Step 5: Create Database and Schema

```bash
# Connect to PostgreSQL as superuser
psql -U postgres -h localhost

# Create database
CREATE DATABASE medical;

# Connect to the medical database
\c medical

# Create schema
CREATE SCHEMA clinical_data;

# Exit psql
\q
```

### Step 6: Run Database Setup Script

```bash
python src/database/setup_database.py
```

This script will:
- Create all required tables
- Set up proper indexes
- Configure constraints and relationships

### Step 7: Load Synthetic Data

```bash
python src/database/simple_enhanced_loader.py
```

This will load approximately 17,000+ clinical records including:
- 107 patients
- 272 organizations
- 272 providers
- 10 payers
- 7,217 encounters
- 3,945 conditions
- 5,750 medications

### Step 8: Validate Database Setup

```bash
python src/database/comprehensive_validator.py
```

This validation script checks:
- Database connectivity
- Table structure integrity
- Referential integrity
- Data quality metrics
- Performance benchmarks

### Step 9: Test Query Performance

```bash
python src/database/nlq_query_tester.py
```

This tests the database with sample NLQ queries and creates performance indexes.

## Database Schema

### Core Tables

#### patients
- **Purpose**: Patient demographic and basic information
- **Key Fields**: id, birth_date, gender, first_name, last_name, address
- **Relationships**: Referenced by encounters, conditions, medications

#### organizations
- **Purpose**: Healthcare organizations (hospitals, clinics)
- **Key Fields**: id, name, address, city, state
- **Relationships**: Referenced by providers, encounters

#### providers
- **Purpose**: Healthcare providers (doctors, nurses)
- **Key Fields**: id, name, speciality, organization_id
- **Relationships**: References organizations, referenced by encounters

#### payers
- **Purpose**: Insurance companies and payment entities
- **Key Fields**: id, name, ownership
- **Relationships**: Referenced by encounters, medications

#### encounters
- **Purpose**: Patient visits and healthcare interactions
- **Key Fields**: id, start_time, patient_id, provider_id, organization_id
- **Relationships**: References patients, providers, organizations, payers

#### conditions
- **Purpose**: Patient diagnoses and medical conditions
- **Key Fields**: start_date, patient_id, code, description
- **Relationships**: References patients, encounters

#### medications
- **Purpose**: Prescribed medications and treatments
- **Key Fields**: start_date, patient_id, description, base_cost
- **Relationships**: References patients, encounters, payers

### Relationships Diagram

```
patients (1) ←→ (M) encounters (M) ←→ (1) organizations
    ↑                    ↑                      ↑
    |                    |                      |
    |                    └─ (M) ←→ (1) providers
    |
    └─ (1) ←→ (M) conditions
    └─ (1) ←→ (M) medications (M) ←→ (1) payers
```

## Performance Optimization

### Indexes Created
The setup automatically creates the following indexes for optimal query performance:

```sql
-- Patient-based queries
CREATE INDEX idx_patients_gender ON clinical_data.patients(gender);

-- Condition-based queries
CREATE INDEX idx_conditions_patient_id ON clinical_data.conditions(patient_id);
CREATE INDEX idx_conditions_description ON clinical_data.conditions(description);

-- Encounter-based queries
CREATE INDEX idx_encounters_patient_id ON clinical_data.encounters(patient_id);
CREATE INDEX idx_encounters_organization_id ON clinical_data.encounters(organization_id);

-- Medication-based queries
CREATE INDEX idx_medications_patient_id ON clinical_data.medications(patient_id);
CREATE INDEX idx_medications_reason_description ON clinical_data.medications(reason_description);
```

### Query Performance Benchmarks

Based on testing with 17,573 records:

| Query Type | Average Time | Expected Performance |
|------------|--------------|---------------------|
| Basic Count | <0.001s | ✅ Excellent |
| Basic Filter | <0.001s | ✅ Excellent |
| Simple Joins | <0.005s | ✅ Excellent |
| Complex Aggregations | <0.030s | ✅ Good |
| Multi-table Joins | <0.010s | ✅ Excellent |

## Data Quality Metrics

### Completeness
- **Overall Completeness**: 85%
- **Critical Fields**: 100% (patient_id, encounter_id, etc.)
- **Optional Fields**: Variable (death_date: 6.5%, suffix: 0.9%)

### Integrity
- **Referential Integrity**: 100% (all foreign keys valid)
- **Data Consistency**: 100% (no temporal inconsistencies)
- **Uniqueness**: 100% (all primary keys unique)

### Clinical Validity
- **Valid Gender Values**: 100%
- **Reasonable Age Ranges**: 100%
- **Valid Date Ranges**: 100%
- **Clinical Code Standards**: ICD-10, RxNorm, SNOMED-CT compliant

## Sample Queries

### Basic Patient Information
```sql
-- Count total patients
SELECT COUNT(*) FROM clinical_data.patients;

-- Get patient demographics
SELECT gender, COUNT(*) as count
FROM clinical_data.patients
GROUP BY gender;
```

### Clinical Conditions
```sql
-- Most common conditions
SELECT description, COUNT(*) as frequency
FROM clinical_data.conditions
GROUP BY description
ORDER BY frequency DESC
LIMIT 10;

-- Patients with diabetes
SELECT DISTINCT p.first_name, p.last_name
FROM clinical_data.patients p
JOIN clinical_data.conditions c ON p.id = c.patient_id
WHERE c.description ILIKE '%diabetes%';
```

### Healthcare Utilization
```sql
-- Encounters per patient
SELECT p.first_name, p.last_name, COUNT(e.id) as encounter_count
FROM clinical_data.patients p
LEFT JOIN clinical_data.encounters e ON p.id = e.patient_id
GROUP BY p.id, p.first_name, p.last_name
ORDER BY encounter_count DESC;

-- Average cost by organization
SELECT o.name, AVG(e.total_claim_cost) as avg_cost
FROM clinical_data.organizations o
JOIN clinical_data.encounters e ON o.id = e.organization_id
WHERE e.total_claim_cost IS NOT NULL
GROUP BY o.name
ORDER BY avg_cost DESC;
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed
**Error**: `psycopg2.OperationalError: could not connect to server`

**Solutions**:
- Verify PostgreSQL service is running
- Check database credentials in `.env` file
- Ensure database `medical` exists
- Verify network connectivity (firewall, port 5432)

#### 2. Permission Denied
**Error**: `psycopg2.errors.InsufficientPrivilege`

**Solutions**:
- Ensure user has CREATE privileges on database
- Grant schema permissions: `GRANT ALL ON SCHEMA clinical_data TO username;`
- Use superuser account for initial setup

#### 3. Table Already Exists
**Error**: `psycopg2.errors.DuplicateTable`

**Solutions**:
- Drop existing tables: `python src/database/drop_tables.py`
- Or use `IF NOT EXISTS` in table creation
- Check for partial installations

#### 4. Data Loading Fails
**Error**: Various data import errors

**Solutions**:
- Verify CSV files exist in `output/csv/` directory
- Check file permissions and encoding
- Ensure sufficient disk space
- Review data validation logs

#### 5. Poor Query Performance
**Symptoms**: Slow query execution times

**Solutions**:
- Run index creation: `python src/database/nlq_query_tester.py`
- Analyze query plans: `EXPLAIN ANALYZE <query>`
- Consider table statistics update: `ANALYZE clinical_data.<table_name>`
- Monitor system resources (RAM, CPU)

### Validation Commands

```bash
# Test database connectivity
python -c "from src.database.comprehensive_validator import ComprehensiveValidator; v = ComprehensiveValidator(); print('✅ Connected' if v.get_database_info()['connection_successful'] else '❌ Failed')"

# Check table row counts
psql -U postgres -d medical -c "
SELECT 
    schemaname,
    tablename,
    n_tup_ins as row_count
FROM pg_stat_user_tables 
WHERE schemaname = 'clinical_data'
ORDER BY n_tup_ins DESC;"

# Verify indexes
psql -U postgres -d medical -c "
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'clinical_data'
ORDER BY tablename, indexname;"
```

## Maintenance

### Regular Tasks

#### Daily
- Monitor query performance logs
- Check database connectivity
- Verify data integrity (automated)

#### Weekly
- Update table statistics: `ANALYZE;`
- Review slow query logs
- Check disk space usage

#### Monthly
- Full database backup
- Performance benchmark testing
- Index usage analysis

### Backup and Recovery

#### Create Backup
```bash
# Full database backup
pg_dump -U postgres -h localhost -d medical > medical_backup_$(date +%Y%m%d).sql

# Schema-only backup
pg_dump -U postgres -h localhost -d medical --schema-only > medical_schema_$(date +%Y%m%d).sql

# Data-only backup
pg_dump -U postgres -h localhost -d medical --data-only > medical_data_$(date +%Y%m%d).sql
```

#### Restore from Backup
```bash
# Restore full database
psql -U postgres -h localhost -d medical < medical_backup_20240125.sql

# Restore schema only
psql -U postgres -h localhost -d medical < medical_schema_20240125.sql
```

## Security Considerations

### Database Security
- Use strong passwords for database users
- Limit network access to database server
- Enable SSL connections for production
- Regular security updates for PostgreSQL

### Application Security
- Store credentials in environment variables
- Use connection pooling for production
- Implement proper error handling
- Log security events

### Data Privacy
- All data is synthetic (no real patient information)
- Suitable for development and testing
- No HIPAA compliance required for synthetic data
- Consider data anonymization for production use

## Next Steps

After successful database setup:

1. **NLQ Model Development**
   - Use database for training text-to-SQL models
   - Implement query generation algorithms
   - Test with various natural language patterns

2. **API Development**
   - Create REST API endpoints
   - Implement query validation
   - Add authentication and authorization

3. **Frontend Development**
   - Build user interface for NLQ input
   - Display query results and visualizations
   - Implement user feedback mechanisms

4. **Production Deployment**
   - Scale database for production load
   - Implement monitoring and alerting
   - Set up automated backups
   - Configure high availability

## Support

### Documentation
- **Database Schema**: `docs/database_schema.md`
- **API Reference**: `docs/api_reference.md`
- **Performance Guide**: `docs/performance_optimization.md`

### Validation Reports
- **Database Validation**: `docs/database_validation_report.md`
- **Query Performance**: `docs/nlq_performance_report.md`
- **Data Quality**: `docs/data_quality_report.md`

### Contact
For technical support or questions:
- Create an issue in the project repository
- Review existing documentation
- Check troubleshooting section above

---

*Last Updated: January 25, 2024*
*Version: 1.0*
*Status: Production Ready*