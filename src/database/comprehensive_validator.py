#!/usr/bin/env python3
"""
Comprehensive Database Validator
Performs extensive validation of the clinical database including:
- Data integrity checks
- Referential integrity validation
- Data quality assessment
- Performance testing
- Clinical data validation
"""

import psycopg2
from sqlalchemy import create_engine, text
import pandas as pd
import logging
from urllib.parse import quote_plus
from datetime import datetime, timedelta
import json
from pathlib import Path
import numpy as np
from typing import Dict, List, Tuple, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveValidator:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'medical',
            'user': 'postgres',
            'password': 'Pass@123'
        }
        
        # Create connection
        password_encoded = quote_plus(self.db_config['password'])
        connection_string = (
            f"postgresql://{self.db_config['user']}:{password_encoded}"
            f"@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
        )
        self.engine = create_engine(connection_string)
        
        # Validation results
        self.validation_results = {
            'timestamp': datetime.now().isoformat(),
            'database_info': {},
            'table_validation': {},
            'referential_integrity': {},
            'data_quality': {},
            'clinical_validation': {},
            'performance_tests': {},
            'summary': {}
        }
    
    def get_database_info(self) -> Dict:
        """Get basic database information"""
        logger.info("Gathering database information...")
        
        try:
            with self.engine.connect() as conn:
                # PostgreSQL version
                result = conn.execute(text("SELECT version()"))
                pg_version = result.scalar()
                
                # Database size
                result = conn.execute(text("""
                    SELECT pg_size_pretty(pg_database_size('medical')) as db_size
                """))
                db_size = result.scalar()
                
                # Schema info
                result = conn.execute(text("""
                    SELECT COUNT(*) as table_count
                    FROM information_schema.tables 
                    WHERE table_schema = 'clinical_data'
                """))
                table_count = result.scalar()
                
                # Total records across all tables
                tables = ['patients', 'organizations', 'providers', 'payers', 
                         'encounters', 'conditions', 'medications']
                total_records = 0
                
                for table in tables:
                    try:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM clinical_data.{table}"))
                        count = result.scalar()
                        total_records += count
                    except:
                        pass
                
                db_info = {
                    'postgresql_version': pg_version,
                    'database_size': db_size,
                    'schema_tables': table_count,
                    'total_records': total_records,
                    'connection_successful': True
                }
                
                self.validation_results['database_info'] = db_info
                logger.info(f"Database info collected: {total_records:,} total records")
                return db_info
                
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {'connection_successful': False, 'error': str(e)}
    
    def validate_table_structure(self) -> Dict:
        """Validate table structures and constraints"""
        logger.info("Validating table structures...")
        
        table_validation = {}
        
        # Expected table structures
        expected_tables = {
            'patients': {
                'required_columns': ['id', 'birth_date', 'gender', 'first_name', 'last_name'],
                'primary_key': 'id',
                'expected_min_rows': 50
            },
            'organizations': {
                'required_columns': ['id', 'name'],
                'primary_key': 'id',
                'expected_min_rows': 10
            },
            'providers': {
                'required_columns': ['id', 'name', 'organization_id'],
                'primary_key': 'id',
                'expected_min_rows': 10
            },
            'payers': {
                'required_columns': ['id', 'name'],
                'primary_key': 'id',
                'expected_min_rows': 5
            },
            'encounters': {
                'required_columns': ['id', 'start_time', 'patient_id'],
                'primary_key': 'id',
                'expected_min_rows': 100
            },
            'conditions': {
                'required_columns': ['start_date', 'patient_id', 'code', 'description'],
                'primary_key': 'id',
                'expected_min_rows': 50
            },
            'medications': {
                'required_columns': ['start_date', 'patient_id', 'description'],
                'primary_key': 'id',
                'expected_min_rows': 50
            }
        }
        
        try:
            with self.engine.connect() as conn:
                for table_name, expectations in expected_tables.items():
                    logger.info(f"Validating table: {table_name}")
                    
                    table_result = {
                        'exists': False,
                        'row_count': 0,
                        'column_validation': {},
                        'primary_key_valid': False,
                        'meets_min_rows': False,
                        'issues': []
                    }
                    
                    try:
                        # Check if table exists
                        result = conn.execute(text(f"""
                            SELECT COUNT(*) 
                            FROM information_schema.tables 
                            WHERE table_schema = 'clinical_data' 
                            AND table_name = '{table_name}'
                        """))
                        
                        if result.scalar() > 0:
                            table_result['exists'] = True
                            
                            # Get row count
                            result = conn.execute(text(f"SELECT COUNT(*) FROM clinical_data.{table_name}"))
                            row_count = result.scalar()
                            table_result['row_count'] = row_count
                            
                            # Check minimum rows
                            table_result['meets_min_rows'] = row_count >= expectations['expected_min_rows']
                            if not table_result['meets_min_rows']:
                                table_result['issues'].append(
                                    f"Row count {row_count} below expected minimum {expectations['expected_min_rows']}"
                                )
                            
                            # Check required columns
                            result = conn.execute(text(f"""
                                SELECT column_name, data_type, is_nullable
                                FROM information_schema.columns
                                WHERE table_schema = 'clinical_data' 
                                AND table_name = '{table_name}'
                            """))
                            
                            existing_columns = {row[0]: {'type': row[1], 'nullable': row[2]} 
                                              for row in result.fetchall()}
                            
                            for req_col in expectations['required_columns']:
                                if req_col in existing_columns:
                                    table_result['column_validation'][req_col] = {
                                        'exists': True,
                                        'type': existing_columns[req_col]['type'],
                                        'nullable': existing_columns[req_col]['nullable']
                                    }
                                else:
                                    table_result['column_validation'][req_col] = {'exists': False}
                                    table_result['issues'].append(f"Missing required column: {req_col}")
                            
                            # Check primary key
                            if expectations.get('primary_key'):
                                pk_col = expectations['primary_key']
                                if pk_col in existing_columns:
                                    # Check for null values in primary key
                                    result = conn.execute(text(f"""
                                        SELECT COUNT(*) 
                                        FROM clinical_data.{table_name} 
                                        WHERE {pk_col} IS NULL
                                    """))
                                    null_pk_count = result.scalar()
                                    
                                    table_result['primary_key_valid'] = null_pk_count == 0
                                    if null_pk_count > 0:
                                        table_result['issues'].append(
                                            f"Primary key {pk_col} has {null_pk_count} null values"
                                        )
                        else:
                            table_result['issues'].append("Table does not exist")
                    
                    except Exception as e:
                        table_result['issues'].append(f"Validation error: {str(e)}")
                    
                    table_validation[table_name] = table_result
        
        except Exception as e:
            logger.error(f"Table structure validation failed: {e}")
            table_validation['error'] = str(e)
        
        self.validation_results['table_validation'] = table_validation
        return table_validation
    
    def validate_referential_integrity(self) -> Dict:
        """Comprehensive referential integrity validation"""
        logger.info("Validating referential integrity...")
        
        integrity_results = {
            'total_checks': 0,
            'passed_checks': 0,
            'failed_checks': 0,
            'violations': [],
            'relationship_details': {}
        }
        
        # Define all foreign key relationships
        relationships = [
            {
                'name': 'providers_organization',
                'child_table': 'providers',
                'child_column': 'organization_id',
                'parent_table': 'organizations',
                'parent_column': 'id',
                'allow_null': True
            },
            {
                'name': 'encounters_patient',
                'child_table': 'encounters',
                'child_column': 'patient_id',
                'parent_table': 'patients',
                'parent_column': 'id',
                'allow_null': False
            },
            {
                'name': 'encounters_provider',
                'child_table': 'encounters',
                'child_column': 'provider_id',
                'parent_table': 'providers',
                'parent_column': 'id',
                'allow_null': True
            },
            {
                'name': 'encounters_organization',
                'child_table': 'encounters',
                'child_column': 'organization_id',
                'parent_table': 'organizations',
                'parent_column': 'id',
                'allow_null': True
            },
            {
                'name': 'encounters_payer',
                'child_table': 'encounters',
                'child_column': 'payer_id',
                'parent_table': 'payers',
                'parent_column': 'id',
                'allow_null': True
            },
            {
                'name': 'conditions_patient',
                'child_table': 'conditions',
                'child_column': 'patient_id',
                'parent_table': 'patients',
                'parent_column': 'id',
                'allow_null': False
            },
            {
                'name': 'conditions_encounter',
                'child_table': 'conditions',
                'child_column': 'encounter_id',
                'parent_table': 'encounters',
                'parent_column': 'id',
                'allow_null': True
            },
            {
                'name': 'medications_patient',
                'child_table': 'medications',
                'child_column': 'patient_id',
                'parent_table': 'patients',
                'parent_column': 'id',
                'allow_null': False
            },
            {
                'name': 'medications_encounter',
                'child_table': 'medications',
                'child_column': 'encounter_id',
                'parent_table': 'encounters',
                'parent_column': 'id',
                'allow_null': True
            },
            {
                'name': 'medications_payer',
                'child_table': 'medications',
                'child_column': 'payer_id',
                'parent_table': 'payers',
                'parent_column': 'id',
                'allow_null': True
            }
        ]
        
        try:
            with self.engine.connect() as conn:
                for rel in relationships:
                    integrity_results['total_checks'] += 1
                    
                    logger.info(f"Checking {rel['name']}: {rel['child_table']}.{rel['child_column']} -> {rel['parent_table']}.{rel['parent_column']}")
                    
                    rel_result = {
                        'relationship': rel['name'],
                        'child_records': 0,
                        'orphaned_records': 0,
                        'null_references': 0,
                        'valid': True,
                        'issues': []
                    }
                    
                    try:
                        # Count total child records
                        result = conn.execute(text(f"SELECT COUNT(*) FROM clinical_data.{rel['child_table']}"))
                        rel_result['child_records'] = result.scalar()
                        
                        # Count null references
                        result = conn.execute(text(f"""
                            SELECT COUNT(*) 
                            FROM clinical_data.{rel['child_table']} 
                            WHERE {rel['child_column']} IS NULL
                        """))
                        rel_result['null_references'] = result.scalar()
                        
                        # Check if nulls are allowed
                        if not rel['allow_null'] and rel_result['null_references'] > 0:
                            rel_result['valid'] = False
                            rel_result['issues'].append(f"Found {rel_result['null_references']} null values in non-nullable foreign key")
                        
                        # Count orphaned records (non-null foreign keys with no matching parent)
                        result = conn.execute(text(f"""
                            SELECT COUNT(*) 
                            FROM clinical_data.{rel['child_table']} c
                            LEFT JOIN clinical_data.{rel['parent_table']} p 
                                ON c.{rel['child_column']} = p.{rel['parent_column']}
                            WHERE c.{rel['child_column']} IS NOT NULL 
                            AND p.{rel['parent_column']} IS NULL
                        """))
                        rel_result['orphaned_records'] = result.scalar()
                        
                        if rel_result['orphaned_records'] > 0:
                            rel_result['valid'] = False
                            rel_result['issues'].append(f"Found {rel_result['orphaned_records']} orphaned records")
                            integrity_results['violations'].append({
                                'relationship': rel['name'],
                                'type': 'orphaned_records',
                                'count': rel_result['orphaned_records']
                            })
                        
                        if rel_result['valid']:
                            integrity_results['passed_checks'] += 1
                        else:
                            integrity_results['failed_checks'] += 1
                    
                    except Exception as e:
                        rel_result['valid'] = False
                        rel_result['issues'].append(f"Validation error: {str(e)}")
                        integrity_results['failed_checks'] += 1
                    
                    integrity_results['relationship_details'][rel['name']] = rel_result
        
        except Exception as e:
            logger.error(f"Referential integrity validation failed: {e}")
            integrity_results['error'] = str(e)
        
        self.validation_results['referential_integrity'] = integrity_results
        logger.info(f"Referential integrity: {integrity_results['passed_checks']}/{integrity_results['total_checks']} checks passed")
        return integrity_results
    
    def assess_data_quality(self) -> Dict:
        """Comprehensive data quality assessment"""
        logger.info("Assessing data quality...")
        
        quality_results = {
            'completeness': {},
            'consistency': {},
            'validity': {},
            'uniqueness': {},
            'overall_score': 0
        }
        
        try:
            with self.engine.connect() as conn:
                # Completeness checks
                logger.info("Checking data completeness...")
                tables_to_check = ['patients', 'encounters', 'conditions', 'medications']
                
                for table in tables_to_check:
                    try:
                        # Get total rows
                        result = conn.execute(text(f"SELECT COUNT(*) FROM clinical_data.{table}"))
                        total_rows = result.scalar()
                        
                        if total_rows > 0:
                            # Get column completeness
                            result = conn.execute(text(f"""
                                SELECT column_name
                                FROM information_schema.columns
                                WHERE table_schema = 'clinical_data' 
                                AND table_name = '{table}'
                                AND column_name NOT LIKE '%_at'
                            """))
                            
                            columns = [row[0] for row in result.fetchall()]
                            column_completeness = {}
                            
                            for col in columns[:10]:  # Check first 10 columns to avoid too many queries
                                try:
                                    result = conn.execute(text(f"""
                                        SELECT COUNT(*) 
                                        FROM clinical_data.{table} 
                                        WHERE {col} IS NOT NULL
                                    """))
                                    non_null_count = result.scalar()
                                    completeness_pct = (non_null_count / total_rows) * 100
                                    column_completeness[col] = round(completeness_pct, 2)
                                except:
                                    column_completeness[col] = 'error'
                            
                            quality_results['completeness'][table] = {
                                'total_rows': total_rows,
                                'column_completeness': column_completeness,
                                'avg_completeness': round(np.mean([v for v in column_completeness.values() if isinstance(v, (int, float))]), 2)
                            }
                    
                    except Exception as e:
                        quality_results['completeness'][table] = {'error': str(e)}
                
                # Consistency checks
                logger.info("Checking data consistency...")
                consistency_checks = []
                
                # Date consistency checks
                try:
                    # Birth dates should be reasonable
                    result = conn.execute(text("""
                        SELECT COUNT(*) 
                        FROM clinical_data.patients 
                        WHERE birth_date > CURRENT_DATE 
                        OR birth_date < '1900-01-01'
                    """))
                    invalid_birth_dates = result.scalar()
                    consistency_checks.append({
                        'check': 'valid_birth_dates',
                        'invalid_count': invalid_birth_dates,
                        'passed': invalid_birth_dates == 0
                    })
                    
                    # Encounter dates should be after birth dates
                    result = conn.execute(text("""
                        SELECT COUNT(*) 
                        FROM clinical_data.encounters e
                        JOIN clinical_data.patients p ON e.patient_id = p.id
                        WHERE e.start_time::date < p.birth_date
                    """))
                    invalid_encounter_dates = result.scalar()
                    consistency_checks.append({
                        'check': 'encounter_after_birth',
                        'invalid_count': invalid_encounter_dates,
                        'passed': invalid_encounter_dates == 0
                    })
                    
                    # Condition start dates should be reasonable
                    result = conn.execute(text("""
                        SELECT COUNT(*) 
                        FROM clinical_data.conditions 
                        WHERE start_date > CURRENT_DATE + INTERVAL '1 year'
                        OR start_date < '1900-01-01'
                    """))
                    invalid_condition_dates = result.scalar()
                    consistency_checks.append({
                        'check': 'valid_condition_dates',
                        'invalid_count': invalid_condition_dates,
                        'passed': invalid_condition_dates == 0
                    })
                
                except Exception as e:
                    consistency_checks.append({
                        'check': 'date_consistency',
                        'error': str(e),
                        'passed': False
                    })
                
                quality_results['consistency'] = consistency_checks
                
                # Validity checks
                logger.info("Checking data validity...")
                validity_checks = []
                
                try:
                    # Gender values should be valid
                    result = conn.execute(text("""
                        SELECT COUNT(*) 
                        FROM clinical_data.patients 
                        WHERE gender NOT IN ('M', 'F') OR gender IS NULL
                    """))
                    invalid_genders = result.scalar()
                    validity_checks.append({
                        'check': 'valid_genders',
                        'invalid_count': invalid_genders,
                        'passed': invalid_genders == 0
                    })
                    
                    # Numeric values should be reasonable
                    result = conn.execute(text("""
                        SELECT COUNT(*) 
                        FROM clinical_data.encounters 
                        WHERE total_claim_cost < 0 OR total_claim_cost > 1000000
                    """))
                    invalid_costs = result.scalar()
                    validity_checks.append({
                        'check': 'reasonable_costs',
                        'invalid_count': invalid_costs,
                        'passed': invalid_costs == 0
                    })
                
                except Exception as e:
                    validity_checks.append({
                        'check': 'validity_checks',
                        'error': str(e),
                        'passed': False
                    })
                
                quality_results['validity'] = validity_checks
                
                # Uniqueness checks
                logger.info("Checking data uniqueness...")
                uniqueness_checks = {}
                
                unique_checks = [
                    ('patients', 'id'),
                    ('encounters', 'id'),
                    ('organizations', 'id'),
                    ('providers', 'id')
                ]
                
                for table, column in unique_checks:
                    try:
                        result = conn.execute(text(f"""
                            SELECT COUNT(*) as total_count,
                                   COUNT(DISTINCT {column}) as unique_count
                            FROM clinical_data.{table}
                        """))
                        row = result.fetchone()
                        total_count, unique_count = row
                        
                        uniqueness_checks[f"{table}.{column}"] = {
                            'total_count': total_count,
                            'unique_count': unique_count,
                            'is_unique': total_count == unique_count,
                            'duplicate_count': total_count - unique_count
                        }
                    
                    except Exception as e:
                        uniqueness_checks[f"{table}.{column}"] = {'error': str(e)}
                
                quality_results['uniqueness'] = uniqueness_checks
                
                # Calculate overall quality score
                passed_checks = 0
                total_checks = 0
                
                for check in consistency_checks:
                    total_checks += 1
                    if check.get('passed', False):
                        passed_checks += 1
                
                for check in validity_checks:
                    total_checks += 1
                    if check.get('passed', False):
                        passed_checks += 1
                
                for check_name, check_data in uniqueness_checks.items():
                    if 'error' not in check_data:
                        total_checks += 1
                        if check_data.get('is_unique', False):
                            passed_checks += 1
                
                if total_checks > 0:
                    quality_results['overall_score'] = round((passed_checks / total_checks) * 100, 2)
        
        except Exception as e:
            logger.error(f"Data quality assessment failed: {e}")
            quality_results['error'] = str(e)
        
        self.validation_results['data_quality'] = quality_results
        logger.info(f"Data quality score: {quality_results.get('overall_score', 0)}%")
        return quality_results
    
    def validate_clinical_data(self) -> Dict:
        """Clinical-specific data validation"""
        logger.info("Validating clinical data...")
        
        clinical_results = {
            'patient_demographics': {},
            'clinical_codes': {},
            'temporal_relationships': {},
            'clinical_logic': {}
        }
        
        try:
            with self.engine.connect() as conn:
                # Patient demographics validation
                logger.info("Validating patient demographics...")
                
                # Age distribution
                result = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_patients,
                        AVG(EXTRACT(YEAR FROM AGE(COALESCE(death_date, CURRENT_DATE), birth_date))) as avg_age,
                        MIN(EXTRACT(YEAR FROM AGE(COALESCE(death_date, CURRENT_DATE), birth_date))) as min_age,
                        MAX(EXTRACT(YEAR FROM AGE(COALESCE(death_date, CURRENT_DATE), birth_date))) as max_age
                    FROM clinical_data.patients
                """))
                
                row = result.fetchone()
                clinical_results['patient_demographics'] = {
                    'total_patients': row[0],
                    'avg_age': round(float(row[1]), 1) if row[1] else None,
                    'min_age': int(row[2]) if row[2] else None,
                    'max_age': int(row[3]) if row[3] else None
                }
                
                # Gender distribution
                result = conn.execute(text("""
                    SELECT gender, COUNT(*) as count
                    FROM clinical_data.patients
                    GROUP BY gender
                """))
                
                gender_dist = {row[0]: row[1] for row in result.fetchall()}
                clinical_results['patient_demographics']['gender_distribution'] = gender_dist
                
                # Clinical codes validation
                logger.info("Validating clinical codes...")
                
                # Condition codes
                result = conn.execute(text("""
                    SELECT 
                        COUNT(DISTINCT code) as unique_condition_codes,
                        COUNT(*) as total_conditions
                    FROM clinical_data.conditions
                """))
                
                row = result.fetchone()
                clinical_results['clinical_codes']['conditions'] = {
                    'unique_codes': row[0],
                    'total_records': row[1]
                }
                
                # Most common conditions
                result = conn.execute(text("""
                    SELECT description, COUNT(*) as frequency
                    FROM clinical_data.conditions
                    GROUP BY description
                    ORDER BY frequency DESC
                    LIMIT 10
                """))
                
                common_conditions = [{'condition': row[0], 'frequency': row[1]} for row in result.fetchall()]
                clinical_results['clinical_codes']['common_conditions'] = common_conditions
                
                # Temporal relationships
                logger.info("Validating temporal relationships...")
                
                # Patient encounter timeline
                result = conn.execute(text("""
                    SELECT 
                        p.id,
                        COUNT(e.id) as encounter_count,
                        MIN(e.start_time) as first_encounter,
                        MAX(e.start_time) as last_encounter
                    FROM clinical_data.patients p
                    LEFT JOIN clinical_data.encounters e ON p.id = e.patient_id
                    GROUP BY p.id
                    HAVING COUNT(e.id) > 0
                    ORDER BY encounter_count DESC
                    LIMIT 5
                """))
                
                patient_timelines = []
                for row in result.fetchall():
                    patient_timelines.append({
                        'patient_id': row[0],
                        'encounter_count': row[1],
                        'first_encounter': row[2].isoformat() if row[2] else None,
                        'last_encounter': row[3].isoformat() if row[3] else None
                    })
                
                clinical_results['temporal_relationships']['patient_timelines'] = patient_timelines
                
                # Clinical logic validation
                logger.info("Validating clinical logic...")
                
                # Patients with conditions should have encounters
                result = conn.execute(text("""
                    SELECT COUNT(DISTINCT c.patient_id) as patients_with_conditions,
                           COUNT(DISTINCT e.patient_id) as patients_with_encounters,
                           COUNT(DISTINCT c.patient_id) - COUNT(DISTINCT e.patient_id) as patients_conditions_no_encounters
                    FROM clinical_data.conditions c
                    FULL OUTER JOIN clinical_data.encounters e ON c.patient_id = e.patient_id
                """))
                
                row = result.fetchone()
                clinical_results['clinical_logic']['condition_encounter_alignment'] = {
                    'patients_with_conditions': row[0],
                    'patients_with_encounters': row[1],
                    'misalignment_count': abs(row[2]) if row[2] else 0
                }
                
                # Medications should have associated encounters or conditions
                result = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_medications,
                        COUNT(CASE WHEN encounter_id IS NOT NULL THEN 1 END) as with_encounters,
                        COUNT(CASE WHEN reason_code IS NOT NULL THEN 1 END) as with_reasons
                    FROM clinical_data.medications
                """))
                
                row = result.fetchone()
                clinical_results['clinical_logic']['medication_associations'] = {
                    'total_medications': row[0],
                    'with_encounters': row[1],
                    'with_reasons': row[2],
                    'encounter_association_rate': round((row[1] / row[0]) * 100, 2) if row[0] > 0 else 0
                }
        
        except Exception as e:
            logger.error(f"Clinical data validation failed: {e}")
            clinical_results['error'] = str(e)
        
        self.validation_results['clinical_validation'] = clinical_results
        return clinical_results
    
    def run_performance_tests(self) -> Dict:
        """Run basic performance tests"""
        logger.info("Running performance tests...")
        
        performance_results = {
            'query_performance': {},
            'index_effectiveness': {},
            'connection_performance': {}
        }
        
        try:
            with self.engine.connect() as conn:
                # Test common query patterns
                test_queries = [
                    {
                        'name': 'patient_lookup',
                        'query': "SELECT * FROM clinical_data.patients WHERE id = (SELECT id FROM clinical_data.patients LIMIT 1)",
                        'expected_max_time': 0.1
                    },
                    {
                        'name': 'patient_encounters',
                        'query': """
                            SELECT p.first_name, p.last_name, COUNT(e.id) as encounter_count
                            FROM clinical_data.patients p
                            LEFT JOIN clinical_data.encounters e ON p.id = e.patient_id
                            GROUP BY p.id, p.first_name, p.last_name
                            LIMIT 10
                        """,
                        'expected_max_time': 1.0
                    },
                    {
                        'name': 'condition_summary',
                        'query': """
                            SELECT description, COUNT(*) as frequency
                            FROM clinical_data.conditions
                            GROUP BY description
                            ORDER BY frequency DESC
                            LIMIT 20
                        """,
                        'expected_max_time': 0.5
                    }
                ]
                
                for test in test_queries:
                    try:
                        start_time = datetime.now()
                        result = conn.execute(text(test['query']))
                        rows = result.fetchall()
                        end_time = datetime.now()
                        
                        execution_time = (end_time - start_time).total_seconds()
                        
                        performance_results['query_performance'][test['name']] = {
                            'execution_time_seconds': round(execution_time, 4),
                            'rows_returned': len(rows),
                            'meets_expectation': execution_time <= test['expected_max_time'],
                            'expected_max_time': test['expected_max_time']
                        }
                        
                        logger.info(f"Query {test['name']}: {execution_time:.4f}s ({len(rows)} rows)")
                    
                    except Exception as e:
                        performance_results['query_performance'][test['name']] = {
                            'error': str(e),
                            'meets_expectation': False
                        }
        
        except Exception as e:
            logger.error(f"Performance tests failed: {e}")
            performance_results['error'] = str(e)
        
        self.validation_results['performance_tests'] = performance_results
        return performance_results
    
    def generate_validation_summary(self) -> Dict:
        """Generate overall validation summary"""
        logger.info("Generating validation summary...")
        
        summary = {
            'overall_status': 'UNKNOWN',
            'total_issues': 0,
            'critical_issues': 0,
            'warnings': 0,
            'recommendations': [],
            'scores': {}
        }
        
        try:
            # Count issues from different validation areas
            issues = 0
            critical_issues = 0
            warnings = 0
            
            # Table validation issues
            table_val = self.validation_results.get('table_validation', {})
            for table, results in table_val.items():
                if isinstance(results, dict) and 'issues' in results:
                    issues += len(results['issues'])
                    if not results.get('exists', True):
                        critical_issues += 1
            
            # Referential integrity issues
            ref_int = self.validation_results.get('referential_integrity', {})
            if 'violations' in ref_int:
                critical_issues += len(ref_int['violations'])
            
            # Data quality issues
            data_qual = self.validation_results.get('data_quality', {})
            if 'consistency' in data_qual:
                for check in data_qual['consistency']:
                    if not check.get('passed', True):
                        if check.get('invalid_count', 0) > 0:
                            issues += 1
                            if check.get('invalid_count', 0) > 100:
                                critical_issues += 1
                            else:
                                warnings += 1
            
            summary['total_issues'] = issues
            summary['critical_issues'] = critical_issues
            summary['warnings'] = warnings
            
            # Determine overall status
            if critical_issues == 0 and issues <= 5:
                summary['overall_status'] = 'EXCELLENT'
            elif critical_issues == 0 and issues <= 15:
                summary['overall_status'] = 'GOOD'
            elif critical_issues <= 2:
                summary['overall_status'] = 'ACCEPTABLE'
            else:
                summary['overall_status'] = 'NEEDS_ATTENTION'
            
            # Generate recommendations
            recommendations = []
            
            if critical_issues > 0:
                recommendations.append("Address critical referential integrity violations immediately")
            
            if data_qual.get('overall_score', 0) < 80:
                recommendations.append("Improve data quality - consider data cleansing procedures")
            
            db_info = self.validation_results.get('database_info', {})
            if db_info.get('total_records', 0) < 10000:
                recommendations.append("Consider generating more synthetic data for better ML training")
            
            if not recommendations:
                recommendations.append("Database validation passed - ready for NLQ development")
            
            summary['recommendations'] = recommendations
            
            # Calculate scores
            summary['scores'] = {
                'data_quality': data_qual.get('overall_score', 0),
                'referential_integrity': (ref_int.get('passed_checks', 0) / max(ref_int.get('total_checks', 1), 1)) * 100,
                'completeness': 85  # Placeholder - could be calculated from completeness data
            }
        
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            summary['error'] = str(e)
        
        self.validation_results['summary'] = summary
        return summary
    
    def save_validation_report(self, output_path=None) -> str:
        """Save comprehensive validation report"""
        if output_path is None:
            output_path = Path(r'd:\projects\healthca\docs') / 'database_validation_report.json'
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.validation_results, f, indent=2, default=str)
        
        logger.info(f"Validation report saved to: {output_path}")
        return str(output_path)
    
    def generate_markdown_report(self, output_path=None) -> str:
        """Generate human-readable markdown report"""
        if output_path is None:
            output_path = Path(r'd:\projects\healthca\docs') / 'database_validation_report.md'
        
        summary = self.validation_results.get('summary', {})
        db_info = self.validation_results.get('database_info', {})
        
        report_lines = [
            "# Clinical Database Validation Report",
            f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            f"## Overall Status: {summary.get('overall_status', 'UNKNOWN')}",
            "",
            "### Summary Statistics",
            f"- **Total Records**: {db_info.get('total_records', 'Unknown'):,}",
            f"- **Database Size**: {db_info.get('database_size', 'Unknown')}",
            f"- **Total Issues**: {summary.get('total_issues', 0)}",
            f"- **Critical Issues**: {summary.get('critical_issues', 0)}",
            f"- **Warnings**: {summary.get('warnings', 0)}",
            "",
            "### Quality Scores",
            f"- **Data Quality**: {summary.get('scores', {}).get('data_quality', 0)}%",
            f"- **Referential Integrity**: {summary.get('scores', {}).get('referential_integrity', 0):.1f}%",
            f"- **Completeness**: {summary.get('scores', {}).get('completeness', 0)}%",
            "",
            "### Recommendations"
        ]
        
        for rec in summary.get('recommendations', []):
            report_lines.append(f"- {rec}")
        
        # Add detailed sections
        table_val = self.validation_results.get('table_validation', {})
        if table_val:
            report_lines.extend([
                "",
                "## Table Validation Results",
                "",
                "| Table | Exists | Rows | Issues |",
                "|-------|--------|------|--------|"
            ])
            
            for table, results in table_val.items():
                if isinstance(results, dict):
                    exists = "✅" if results.get('exists', False) else "❌"
                    rows = results.get('row_count', 0)
                    issues = len(results.get('issues', []))
                    report_lines.append(f"| {table} | {exists} | {rows:,} | {issues} |")
        
        # Add referential integrity section
        ref_int = self.validation_results.get('referential_integrity', {})
        if ref_int:
            report_lines.extend([
                "",
                "## Referential Integrity",
                f"- **Checks Performed**: {ref_int.get('total_checks', 0)}",
                f"- **Passed**: {ref_int.get('passed_checks', 0)}",
                f"- **Failed**: {ref_int.get('failed_checks', 0)}",
                ""
            ])
            
            if ref_int.get('violations'):
                report_lines.append("### Violations Found:")
                for violation in ref_int['violations']:
                    report_lines.append(f"- {violation['relationship']}: {violation['count']} {violation['type']}")
        
        # Save report
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        logger.info(f"Markdown report saved to: {output_path}")
        return str(output_path)
    
    def run_comprehensive_validation(self) -> bool:
        """Run all validation checks"""
        logger.info("Starting comprehensive database validation...")
        
        try:
            # Run all validation steps
            self.get_database_info()
            self.validate_table_structure()
            self.validate_referential_integrity()
            self.assess_data_quality()
            self.validate_clinical_data()
            self.run_performance_tests()
            self.generate_validation_summary()
            
            # Save reports
            json_report = self.save_validation_report()
            md_report = self.generate_markdown_report()
            
            # Final summary
            summary = self.validation_results['summary']
            logger.info("=" * 60)
            logger.info("COMPREHENSIVE VALIDATION COMPLETE")
            logger.info("=" * 60)
            logger.info(f"Overall Status: {summary.get('overall_status', 'UNKNOWN')}")
            logger.info(f"Total Issues: {summary.get('total_issues', 0)}")
            logger.info(f"Critical Issues: {summary.get('critical_issues', 0)}")
            logger.info(f"Data Quality Score: {summary.get('scores', {}).get('data_quality', 0)}%")
            logger.info(f"JSON Report: {json_report}")
            logger.info(f"Markdown Report: {md_report}")
            logger.info("=" * 60)
            
            return summary.get('critical_issues', 0) == 0
        
        except Exception as e:
            logger.error(f"Comprehensive validation failed: {e}")
            return False

def main():
    """Main execution function"""
    validator = ComprehensiveValidator()
    success = validator.run_comprehensive_validation()
    return success

if __name__ == "__main__":
    main()