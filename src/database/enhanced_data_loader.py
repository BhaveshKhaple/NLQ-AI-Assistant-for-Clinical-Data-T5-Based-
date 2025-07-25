#!/usr/bin/env python3
"""
Enhanced Data Loader for Clinical Database
Comprehensive data loading with error handling, batch processing, and validation
"""

import os
import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text, inspect
import logging
from urllib.parse import quote_plus
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import time
from typing import Dict, List, Optional, Tuple
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_loading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedDataLoader:
    def __init__(self, csv_dir=r'd:\projects\healthca\output\csv'):
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
        self.engine = create_engine(connection_string, pool_pre_ping=True)
        self.csv_dir = Path(csv_dir)
        
        # Loading configuration
        self.batch_size = 1000
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        
        # Statistics tracking
        self.loading_stats = {
            'start_time': None,
            'end_time': None,
            'tables_processed': 0,
            'total_rows_loaded': 0,
            'errors': [],
            'warnings': [],
            'table_stats': {}
        }
        
        # Table loading order (respects foreign key dependencies)
        self.loading_order = [
            'organizations',
            'payers', 
            'patients',
            'providers',
            'encounters',
            'conditions',
            'medications',
            'procedures',
            'observations',
            'immunizations',
            'allergies',
            'care_plans'
        ]
        
        # Column mappings for each table
        self.column_mappings = {
            'patients': {
                'ID': 'id',
                'BIRTHDATE': 'birth_date',
                'DEATHDATE': 'death_date',
                'SSN': 'ssn',
                'DRIVERS': 'drivers',
                'PASSPORT': 'passport',
                'PREFIX': 'prefix',
                'FIRST': 'first_name',
                'MIDDLE': 'middle_name',
                'LAST': 'last_name',
                'SUFFIX': 'suffix',
                'MAIDEN': 'maiden_name',
                'MARITAL': 'marital_status',
                'RACE': 'race',
                'ETHNICITY': 'ethnicity',
                'GENDER': 'gender',
                'BIRTHPLACE': 'birth_place',
                'ADDRESS': 'address',
                'CITY': 'city',
                'STATE': 'state',
                'COUNTY': 'county',
                'FIPS': 'fips',
                'ZIP': 'zip',
                'LAT': 'latitude',
                'LON': 'longitude',
                'HEALTHCARE_EXPENSES': 'healthcare_expenses',
                'HEALTHCARE_COVERAGE': 'healthcare_coverage',
                'INCOME': 'income'
            },
            'organizations': {
                'ID': 'id',
                'NAME': 'name',
                'ADDRESS': 'address',
                'CITY': 'city',
                'STATE': 'state',
                'ZIP': 'zip',
                'LAT': 'latitude',
                'LON': 'longitude',
                'PHONE': 'phone',
                'REVENUE': 'revenue',
                'UTILIZATION': 'utilization'
            },
            'providers': {
                'ID': 'id',
                'ORGANIZATION': 'organization_id',
                'NAME': 'name',
                'GENDER': 'gender',
                'SPECIALITY': 'speciality',
                'ADDRESS': 'address',
                'CITY': 'city',
                'STATE': 'state',
                'ZIP': 'zip',
                'LAT': 'latitude',
                'LON': 'longitude',
                'ENCOUNTERS': 'utilization'
            },
            'payers': {
                'ID': 'id',
                'NAME': 'name',
                'OWNERSHIP': 'ownership',
                'ADDRESS': 'address',
                'CITY': 'city',
                'STATE': 'state',
                'ZIP': 'zip',
                'PHONE': 'phone',
                'AMOUNT_COVERED': 'amount_covered',
                'AMOUNT_UNCOVERED': 'amount_uncovered',
                'REVENUE': 'revenue',
                'COVERED_ENCOUNTERS': 'covered_encounters',
                'UNCOVERED_ENCOUNTERS': 'uncovered_encounters',
                'COVERED_MEDICATIONS': 'covered_medications',
                'UNCOVERED_MEDICATIONS': 'uncovered_medications',
                'COVERED_PROCEDURES': 'covered_procedures',
                'UNCOVERED_PROCEDURES': 'uncovered_procedures',
                'COVERED_IMMUNIZATIONS': 'covered_immunizations',
                'UNCOVERED_IMMUNIZATIONS': 'uncovered_immunizations',
                'UNIQUE_CUSTOMERS': 'unique_customers',
                'QOLS_AVG': 'qols_avg',
                'MEMBER_MONTHS': 'member_months'
            },
            'encounters': {
                'ID': 'id',
                'START': 'start_time',
                'STOP': 'stop_time',
                'PATIENT': 'patient_id',
                'ORGANIZATION': 'organization_id',
                'PROVIDER': 'provider_id',
                'PAYER': 'payer_id',
                'ENCOUNTERCLASS': 'encounter_class',
                'CODE': 'code',
                'DESCRIPTION': 'description',
                'BASE_ENCOUNTER_COST': 'base_encounter_cost',
                'TOTAL_CLAIM_COST': 'total_claim_cost',
                'PAYER_COVERAGE': 'payer_coverage',
                'REASONCODE': 'reason_code',
                'REASONDESCRIPTION': 'reason_description'
            },
            'conditions': {
                'START': 'start_date',
                'STOP': 'stop_date',
                'PATIENT': 'patient_id',
                'ENCOUNTER': 'encounter_id',
                'SYSTEM': 'system',
                'CODE': 'code',
                'DESCRIPTION': 'description'
            },
            'medications': {
                'START': 'start_date',
                'STOP': 'stop_date',
                'PATIENT': 'patient_id',
                'PAYER': 'payer_id',
                'ENCOUNTER': 'encounter_id',
                'CODE': 'code',
                'DESCRIPTION': 'description',
                'BASE_COST': 'base_cost',
                'PAYER_COVERAGE': 'payer_coverage',
                'DISPENSES': 'dispenses',
                'TOTALCOST': 'total_cost',
                'REASONCODE': 'reason_code',
                'REASONDESCRIPTION': 'reason_description'
            }
        }
    
    def validate_database_connection(self) -> bool:
        """Validate database connection and schema"""
        try:
            with self.engine.connect() as conn:
                # Test connection
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()
                logger.info(f"Connected to: {version}")
                
                # Check if schema exists
                result = conn.execute(text(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'clinical_data'"
                ))
                if not result.fetchone():
                    logger.error("Schema 'clinical_data' does not exist")
                    return False
                
                logger.info("Database connection and schema validated successfully")
                return True
                
        except Exception as e:
            logger.error(f"Database validation failed: {e}")
            return False
    
    def get_table_schema(self, table_name: str) -> Dict:
        """Get table schema information"""
        try:
            inspector = inspect(self.engine)
            columns = inspector.get_columns(table_name, schema='clinical_data')
            pk_constraint = inspector.get_pk_constraint(table_name, schema='clinical_data')
            foreign_keys = inspector.get_foreign_keys(table_name, schema='clinical_data')
            
            return {
                'columns': {col['name']: col for col in columns},
                'primary_keys': pk_constraint.get('constrained_columns', []),
                'foreign_keys': foreign_keys
            }
        except Exception as e:
            logger.error(f"Failed to get schema for {table_name}: {e}")
            return {}
    
    def validate_csv_file(self, csv_path: Path, table_name: str) -> Tuple[bool, List[str]]:
        """Validate CSV file before loading"""
        issues = []
        
        try:
            # Check if file exists
            if not csv_path.exists():
                issues.append(f"CSV file does not exist: {csv_path}")
                return False, issues
            
            # Check file size
            file_size = csv_path.stat().st_size
            if file_size == 0:
                issues.append(f"CSV file is empty: {csv_path}")
                return False, issues
            
            # Read header to validate structure
            df_sample = pd.read_csv(csv_path, nrows=5, low_memory=False)
            
            if len(df_sample) == 0:
                issues.append(f"CSV file has no data rows: {csv_path}")
                return False, issues
            
            # Check column mapping
            if table_name in self.column_mappings:
                expected_columns = set(self.column_mappings[table_name].keys())
                actual_columns = set(df_sample.columns.str.upper())
                
                missing_columns = expected_columns - actual_columns
                if missing_columns:
                    issues.append(f"Missing columns: {missing_columns}")
            
            logger.info(f"CSV validation passed for {csv_path.name}")
            return True, issues
            
        except Exception as e:
            issues.append(f"Error validating CSV: {e}")
            return False, issues
    
    def clean_dataframe(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """Clean and prepare dataframe for loading"""
        logger.info(f"Cleaning dataframe for {table_name} ({len(df)} rows)")
        
        # Apply column mapping
        if table_name in self.column_mappings:
            df.columns = df.columns.str.upper()
            df = df.rename(columns=self.column_mappings[table_name])
        
        # Handle missing values
        df = df.replace([np.inf, -np.inf], None)
        df = df.where(pd.notnull(df), None)
        
        # Convert data types based on table schema
        schema = self.get_table_schema(table_name)
        
        for col_name, col_info in schema.get('columns', {}).items():
            if col_name in df.columns:
                col_type = str(col_info['type']).lower()
                
                try:
                    if 'timestamp' in col_type or 'datetime' in col_type:
                        df[col_name] = pd.to_datetime(df[col_name], errors='coerce')
                    elif 'date' in col_type:
                        df[col_name] = pd.to_datetime(df[col_name], errors='coerce').dt.date
                    elif 'numeric' in col_type or 'decimal' in col_type or 'float' in col_type:
                        df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
                    elif 'integer' in col_type or 'int' in col_type:
                        df[col_name] = pd.to_numeric(df[col_name], errors='coerce', downcast='integer')
                    elif 'boolean' in col_type or 'bool' in col_type:
                        df[col_name] = df[col_name].astype('boolean')
                        
                except Exception as e:
                    logger.warning(f"Failed to convert column {col_name} to {col_type}: {e}")
        
        # Remove rows with null primary keys
        pk_columns = schema.get('primary_keys', [])
        for pk_col in pk_columns:
            if pk_col in df.columns:
                initial_count = len(df)
                df = df.dropna(subset=[pk_col])
                dropped_count = initial_count - len(df)
                if dropped_count > 0:
                    logger.warning(f"Dropped {dropped_count} rows with null primary key {pk_col}")
        
        logger.info(f"Dataframe cleaned: {len(df)} rows remaining")
        return df
    
    def load_table_batch(self, df_batch: pd.DataFrame, table_name: str, batch_num: int) -> Tuple[bool, int]:
        """Load a single batch of data"""
        try:
            rows_loaded = df_batch.to_sql(
                table_name, 
                self.engine, 
                schema='clinical_data',
                if_exists='append', 
                index=False, 
                method='multi',
                chunksize=500
            )
            
            logger.info(f"Batch {batch_num} loaded successfully: {len(df_batch)} rows")
            return True, len(df_batch)
            
        except Exception as e:
            logger.error(f"Failed to load batch {batch_num}: {e}")
            return False, 0
    
    def load_table_with_retry(self, csv_path: Path, table_name: str) -> Dict:
        """Load table with retry logic and comprehensive error handling"""
        start_time = time.time()
        table_stats = {
            'csv_file': csv_path.name,
            'table_name': table_name,
            'start_time': datetime.now().isoformat(),
            'total_rows_in_csv': 0,
            'rows_loaded': 0,
            'batches_processed': 0,
            'errors': [],
            'warnings': [],
            'success': False,
            'duration_seconds': 0
        }
        
        try:
            # Validate CSV file
            is_valid, issues = self.validate_csv_file(csv_path, table_name)
            if not is_valid:
                table_stats['errors'].extend(issues)
                return table_stats
            
            # Read CSV file
            logger.info(f"Reading CSV file: {csv_path.name}")
            df = pd.read_csv(csv_path, low_memory=False)
            table_stats['total_rows_in_csv'] = len(df)
            
            if len(df) == 0:
                logger.warning(f"No data to load for {table_name}")
                table_stats['warnings'].append("No data in CSV file")
                table_stats['success'] = True
                return table_stats
            
            # Clean dataframe
            df_clean = self.clean_dataframe(df, table_name)
            
            if len(df_clean) == 0:
                logger.warning(f"No valid data after cleaning for {table_name}")
                table_stats['warnings'].append("No valid data after cleaning")
                table_stats['success'] = True
                return table_stats
            
            # Truncate table before loading
            logger.info(f"Truncating table: {table_name}")
            with self.engine.connect() as conn:
                conn.execute(text(f"TRUNCATE TABLE clinical_data.{table_name} CASCADE"))
                conn.commit()
            
            # Load data in batches
            total_batches = (len(df_clean) + self.batch_size - 1) // self.batch_size
            logger.info(f"Loading {len(df_clean)} rows in {total_batches} batches")
            
            for batch_num in range(total_batches):
                start_idx = batch_num * self.batch_size
                end_idx = min((batch_num + 1) * self.batch_size, len(df_clean))
                df_batch = df_clean.iloc[start_idx:end_idx]
                
                # Retry logic for each batch
                for attempt in range(self.max_retries):
                    try:
                        success, rows_loaded = self.load_table_batch(df_batch, table_name, batch_num + 1)
                        if success:
                            table_stats['rows_loaded'] += rows_loaded
                            table_stats['batches_processed'] += 1
                            break
                        else:
                            if attempt < self.max_retries - 1:
                                logger.warning(f"Retrying batch {batch_num + 1} in {self.retry_delay} seconds...")
                                time.sleep(self.retry_delay)
                            else:
                                table_stats['errors'].append(f"Failed to load batch {batch_num + 1} after {self.max_retries} attempts")
                    
                    except Exception as e:
                        error_msg = f"Batch {batch_num + 1} attempt {attempt + 1} failed: {e}"
                        logger.error(error_msg)
                        if attempt == self.max_retries - 1:
                            table_stats['errors'].append(error_msg)
                        else:
                            time.sleep(self.retry_delay)
            
            # Verify loaded data
            with self.engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM clinical_data.{table_name}"))
                actual_count = result.scalar()
                
                if actual_count != table_stats['rows_loaded']:
                    logger.warning(f"Row count mismatch: expected {table_stats['rows_loaded']}, got {actual_count}")
                    table_stats['warnings'].append(f"Row count mismatch: expected {table_stats['rows_loaded']}, got {actual_count}")
                    table_stats['rows_loaded'] = actual_count
            
            table_stats['success'] = len(table_stats['errors']) == 0
            
        except Exception as e:
            error_msg = f"Unexpected error loading {table_name}: {e}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            table_stats['errors'].append(error_msg)
        
        finally:
            table_stats['duration_seconds'] = time.time() - start_time
            table_stats['end_time'] = datetime.now().isoformat()
        
        return table_stats
    
    def validate_referential_integrity(self) -> Dict:
        """Validate foreign key relationships"""
        logger.info("Validating referential integrity...")
        
        integrity_results = {
            'checks_performed': 0,
            'violations_found': 0,
            'details': []
        }
        
        # Define key relationships to check
        relationships = [
            ('providers', 'organization_id', 'organizations', 'id'),
            ('encounters', 'patient_id', 'patients', 'id'),
            ('encounters', 'organization_id', 'organizations', 'id'),
            ('encounters', 'provider_id', 'providers', 'id'),
            ('encounters', 'payer_id', 'payers', 'id'),
            ('conditions', 'patient_id', 'patients', 'id'),
            ('conditions', 'encounter_id', 'encounters', 'id'),
            ('medications', 'patient_id', 'patients', 'id'),
            ('medications', 'encounter_id', 'encounters', 'id'),
            ('medications', 'payer_id', 'payers', 'id')
        ]
        
        try:
            with self.engine.connect() as conn:
                for child_table, child_col, parent_table, parent_col in relationships:
                    integrity_results['checks_performed'] += 1
                    
                    # Check for orphaned records
                    query = text(f"""
                        SELECT COUNT(*) 
                        FROM clinical_data.{child_table} c
                        LEFT JOIN clinical_data.{parent_table} p ON c.{child_col} = p.{parent_col}
                        WHERE c.{child_col} IS NOT NULL AND p.{parent_col} IS NULL
                    """)
                    
                    result = conn.execute(query)
                    violation_count = result.scalar()
                    
                    if violation_count > 0:
                        integrity_results['violations_found'] += violation_count
                        integrity_results['details'].append({
                            'child_table': child_table,
                            'child_column': child_col,
                            'parent_table': parent_table,
                            'parent_column': parent_col,
                            'orphaned_records': violation_count
                        })
                        logger.warning(f"Found {violation_count} orphaned records in {child_table}.{child_col}")
                    else:
                        logger.info(f"✅ {child_table}.{child_col} → {parent_table}.{parent_col}: OK")
        
        except Exception as e:
            logger.error(f"Error validating referential integrity: {e}")
            integrity_results['error'] = str(e)
        
        return integrity_results
    
    def generate_loading_report(self) -> str:
        """Generate comprehensive loading report"""
        report_lines = [
            "# Clinical Database Loading Report",
            f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "## Loading Summary",
            f"- **Start Time**: {self.loading_stats['start_time']}",
            f"- **End Time**: {self.loading_stats['end_time']}",
            f"- **Duration**: {(datetime.fromisoformat(self.loading_stats['end_time']) - datetime.fromisoformat(self.loading_stats['start_time'])).total_seconds():.1f} seconds",
            f"- **Tables Processed**: {self.loading_stats['tables_processed']}",
            f"- **Total Rows Loaded**: {self.loading_stats['total_rows_loaded']:,}",
            f"- **Total Errors**: {len(self.loading_stats['errors'])}",
            f"- **Total Warnings**: {len(self.loading_stats['warnings'])}",
            "",
            "## Table Loading Results",
            "",
            "| Table | CSV Rows | Loaded Rows | Batches | Success | Duration (s) |",
            "|-------|----------|-------------|---------|---------|--------------|"
        ]
        
        for table_name, stats in self.loading_stats['table_stats'].items():
            success_icon = "✅" if stats['success'] else "❌"
            report_lines.append(
                f"| {table_name} | {stats['total_rows_in_csv']:,} | {stats['rows_loaded']:,} | "
                f"{stats['batches_processed']} | {success_icon} | {stats['duration_seconds']:.1f} |"
            )
        
        # Add detailed error information
        if self.loading_stats['errors']:
            report_lines.extend([
                "",
                "## Errors Encountered",
                ""
            ])
            for error in self.loading_stats['errors']:
                report_lines.append(f"- {error}")
        
        # Add warnings
        if self.loading_stats['warnings']:
            report_lines.extend([
                "",
                "## Warnings",
                ""
            ])
            for warning in self.loading_stats['warnings']:
                report_lines.append(f"- {warning}")
        
        return '\n'.join(report_lines)
    
    def load_all_tables(self) -> bool:
        """Load all tables in the correct order"""
        self.loading_stats['start_time'] = datetime.now().isoformat()
        logger.info("Starting comprehensive data loading process...")
        
        # Validate database connection
        if not self.validate_database_connection():
            return False
        
        # Load tables in dependency order
        for table_name in self.loading_order:
            csv_file = self.csv_dir / f"{table_name}.csv"
            
            if not csv_file.exists():
                logger.warning(f"CSV file not found: {csv_file}")
                self.loading_stats['warnings'].append(f"CSV file not found: {csv_file}")
                continue
            
            logger.info(f"Loading table: {table_name}")
            table_stats = self.load_table_with_retry(csv_file, table_name)
            
            self.loading_stats['table_stats'][table_name] = table_stats
            self.loading_stats['tables_processed'] += 1
            self.loading_stats['total_rows_loaded'] += table_stats['rows_loaded']
            
            if table_stats['errors']:
                self.loading_stats['errors'].extend(table_stats['errors'])
            if table_stats['warnings']:
                self.loading_stats['warnings'].extend(table_stats['warnings'])
            
            if not table_stats['success']:
                logger.error(f"Failed to load {table_name}")
            else:
                logger.info(f"✅ Successfully loaded {table_name}: {table_stats['rows_loaded']} rows")
        
        self.loading_stats['end_time'] = datetime.now().isoformat()
        
        # Validate referential integrity
        logger.info("Performing referential integrity validation...")
        integrity_results = self.validate_referential_integrity()
        self.loading_stats['integrity_check'] = integrity_results
        
        # Generate and save report
        report_content = self.generate_loading_report()
        report_path = Path(r'd:\projects\healthca\docs') / 'data_loading_report.md'
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Loading report saved to: {report_path}")
        
        # Final summary
        success = len(self.loading_stats['errors']) == 0
        logger.info("=" * 60)
        logger.info("DATA LOADING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Status: {'SUCCESS' if success else 'COMPLETED WITH ERRORS'}")
        logger.info(f"Tables processed: {self.loading_stats['tables_processed']}")
        logger.info(f"Total rows loaded: {self.loading_stats['total_rows_loaded']:,}")
        logger.info(f"Errors: {len(self.loading_stats['errors'])}")
        logger.info(f"Warnings: {len(self.loading_stats['warnings'])}")
        logger.info("=" * 60)
        
        return success

def main():
    """Main execution function"""
    loader = EnhancedDataLoader()
    success = loader.load_all_tables()
    return success

if __name__ == "__main__":
    main()