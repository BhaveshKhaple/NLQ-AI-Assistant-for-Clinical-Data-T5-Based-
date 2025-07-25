#!/usr/bin/env python3
"""
Simple Enhanced Data Loader - Based on working final_corrected_import.py
Enhanced with better error handling and validation
"""

import os
import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
import logging
from urllib.parse import quote_plus
import numpy as np
from datetime import datetime
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleEnhancedLoader:
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
        self.csv_dir = r'd:\projects\healthca\output\csv'
        
        # Statistics tracking
        self.stats = {
            'start_time': None,
            'end_time': None,
            'tables_loaded': 0,
            'total_rows': 0,
            'errors': [],
            'warnings': []
        }
    
    def truncate_table(self, table_name):
        """Truncate table instead of dropping to preserve structure"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text(f"TRUNCATE TABLE clinical_data.{table_name} CASCADE"))
                conn.commit()
                logger.info(f"Truncated table: {table_name}")
                return True
        except Exception as e:
            logger.error(f"Failed to truncate {table_name}: {e}")
            return False
    
    def validate_and_clean_data(self, df, table_name):
        """Validate and clean dataframe"""
        logger.info(f"Validating and cleaning {table_name} data ({len(df)} rows)")
        
        # Replace infinite values and NaN
        df = df.replace([np.inf, -np.inf], None)
        df = df.where(pd.notnull(df), None)
        
        # Log data quality issues
        null_counts = df.isnull().sum()
        if null_counts.sum() > 0:
            logger.info(f"Null values found in {table_name}:")
            for col, count in null_counts[null_counts > 0].items():
                logger.info(f"  {col}: {count} nulls ({count/len(df)*100:.1f}%)")
        
        return df
    
    def load_with_batch_processing(self, df, table_name, batch_size=1000):
        """Load data with batch processing and error handling"""
        total_rows = len(df)
        loaded_rows = 0
        
        if total_rows == 0:
            logger.warning(f"No data to load for {table_name}")
            return 0
        
        # Calculate number of batches
        num_batches = (total_rows + batch_size - 1) // batch_size
        logger.info(f"Loading {total_rows} rows in {num_batches} batches")
        
        for batch_num in range(num_batches):
            start_idx = batch_num * batch_size
            end_idx = min((batch_num + 1) * batch_size, total_rows)
            batch_df = df.iloc[start_idx:end_idx]
            
            try:
                batch_df.to_sql(
                    table_name, 
                    self.engine, 
                    schema='clinical_data',
                    if_exists='append', 
                    index=False, 
                    method='multi',
                    chunksize=500
                )
                loaded_rows += len(batch_df)
                logger.info(f"Batch {batch_num + 1}/{num_batches} loaded: {len(batch_df)} rows")
                
            except Exception as e:
                logger.error(f"Failed to load batch {batch_num + 1}: {e}")
                self.stats['errors'].append(f"{table_name} batch {batch_num + 1}: {str(e)}")
                # Continue with next batch instead of failing completely
        
        return loaded_rows
    
    def import_patients(self):
        """Import patients with enhanced error handling"""
        csv_path = os.path.join(self.csv_dir, 'patients.csv')
        
        try:
            logger.info("Loading patients.csv...")
            df = pd.read_csv(csv_path, low_memory=False)
            logger.info(f"Read {len(df)} rows from patients.csv")
            
            # Column mapping
            df.columns = df.columns.str.upper()
            column_mapping = {
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
            }
            
            df = df.rename(columns=column_mapping)
            
            # Convert data types
            date_columns = ['birth_date', 'death_date']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            numeric_columns = ['latitude', 'longitude', 'healthcare_expenses', 'healthcare_coverage', 'income']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Validate and clean
            df = self.validate_and_clean_data(df, 'patients')
            
            # Keep only expected columns
            expected_columns = list(column_mapping.values())
            df = df[[col for col in expected_columns if col in df.columns]]
            
            # Truncate and load
            if self.truncate_table('patients'):
                loaded_rows = self.load_with_batch_processing(df, 'patients')
                logger.info(f"Successfully loaded {loaded_rows} patients")
                return loaded_rows
            
        except Exception as e:
            logger.error(f"Failed to import patients: {e}")
            self.stats['errors'].append(f"patients: {str(e)}")
            return 0
    
    def import_organizations(self):
        """Import organizations"""
        csv_path = os.path.join(self.csv_dir, 'organizations.csv')
        
        try:
            logger.info("Loading organizations.csv...")
            df = pd.read_csv(csv_path, low_memory=False)
            logger.info(f"Read {len(df)} rows from organizations.csv")
            
            # Column mapping
            df.columns = df.columns.str.upper()
            column_mapping = {
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
            }
            
            df = df.rename(columns=column_mapping)
            
            # Convert numeric columns
            numeric_columns = ['latitude', 'longitude', 'revenue', 'utilization']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Validate and clean
            df = self.validate_and_clean_data(df, 'organizations')
            
            # Keep only expected columns
            expected_columns = list(column_mapping.values())
            df = df[[col for col in expected_columns if col in df.columns]]
            
            # Truncate and load
            if self.truncate_table('organizations'):
                loaded_rows = self.load_with_batch_processing(df, 'organizations')
                logger.info(f"Successfully loaded {loaded_rows} organizations")
                return loaded_rows
            
        except Exception as e:
            logger.error(f"Failed to import organizations: {e}")
            self.stats['errors'].append(f"organizations: {str(e)}")
            return 0
    
    def import_providers(self):
        """Import providers"""
        csv_path = os.path.join(self.csv_dir, 'providers.csv')
        
        try:
            logger.info("Loading providers.csv...")
            df = pd.read_csv(csv_path, low_memory=False)
            logger.info(f"Read {len(df)} rows from providers.csv")
            
            # Column mapping
            df.columns = df.columns.str.upper()
            column_mapping = {
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
            }
            
            df = df.rename(columns=column_mapping)
            
            # Convert numeric columns
            numeric_columns = ['latitude', 'longitude', 'utilization']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Validate and clean
            df = self.validate_and_clean_data(df, 'providers')
            
            # Keep only expected columns
            expected_columns = list(column_mapping.values())
            df = df[[col for col in expected_columns if col in df.columns]]
            
            # Truncate and load
            if self.truncate_table('providers'):
                loaded_rows = self.load_with_batch_processing(df, 'providers')
                logger.info(f"Successfully loaded {loaded_rows} providers")
                return loaded_rows
            
        except Exception as e:
            logger.error(f"Failed to import providers: {e}")
            self.stats['errors'].append(f"providers: {str(e)}")
            return 0
    
    def import_payers(self):
        """Import payers"""
        csv_path = os.path.join(self.csv_dir, 'payers.csv')
        
        try:
            logger.info("Loading payers.csv...")
            df = pd.read_csv(csv_path, low_memory=False)
            logger.info(f"Read {len(df)} rows from payers.csv")
            
            # Column mapping - only map columns that exist in both CSV and database
            df.columns = df.columns.str.upper()
            
            # Check what columns actually exist in the CSV
            logger.info(f"Available columns in payers.csv: {list(df.columns)}")
            
            # Basic mapping for core columns
            column_mapping = {
                'ID': 'id',
                'NAME': 'name'
            }
            
            # Add optional columns if they exist
            optional_mappings = {
                'OWNERSHIP': 'ownership',
                'ADDRESS': 'address',
                'CITY': 'city',
                'STATE': 'state',
                'ZIP': 'zip',
                'PHONE': 'phone'
            }
            
            for csv_col, db_col in optional_mappings.items():
                if csv_col in df.columns:
                    column_mapping[csv_col] = db_col
            
            df = df.rename(columns=column_mapping)
            
            # Validate and clean
            df = self.validate_and_clean_data(df, 'payers')
            
            # Keep only mapped columns
            df = df[[col for col in column_mapping.values() if col in df.columns]]
            
            # Truncate and load
            if self.truncate_table('payers'):
                loaded_rows = self.load_with_batch_processing(df, 'payers')
                logger.info(f"Successfully loaded {loaded_rows} payers")
                return loaded_rows
            
        except Exception as e:
            logger.error(f"Failed to import payers: {e}")
            self.stats['errors'].append(f"payers: {str(e)}")
            return 0
    
    def import_encounters(self):
        """Import encounters"""
        csv_path = os.path.join(self.csv_dir, 'encounters.csv')
        
        try:
            logger.info("Loading encounters.csv...")
            df = pd.read_csv(csv_path, low_memory=False)
            logger.info(f"Read {len(df)} rows from encounters.csv")
            
            # Column mapping
            df.columns = df.columns.str.upper()
            column_mapping = {
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
            }
            
            df = df.rename(columns=column_mapping)
            
            # Convert timestamps
            df['start_time'] = pd.to_datetime(df['start_time'], errors='coerce')
            df['stop_time'] = pd.to_datetime(df['stop_time'], errors='coerce')
            
            # Convert numeric columns
            numeric_columns = ['base_encounter_cost', 'total_claim_cost', 'payer_coverage']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Validate and clean
            df = self.validate_and_clean_data(df, 'encounters')
            
            # Keep only expected columns
            expected_columns = list(column_mapping.values())
            df = df[[col for col in expected_columns if col in df.columns]]
            
            # Truncate and load
            if self.truncate_table('encounters'):
                loaded_rows = self.load_with_batch_processing(df, 'encounters')
                logger.info(f"Successfully loaded {loaded_rows} encounters")
                return loaded_rows
            
        except Exception as e:
            logger.error(f"Failed to import encounters: {e}")
            self.stats['errors'].append(f"encounters: {str(e)}")
            return 0
    
    def import_conditions(self):
        """Import conditions"""
        csv_path = os.path.join(self.csv_dir, 'conditions.csv')
        
        try:
            logger.info("Loading conditions.csv...")
            df = pd.read_csv(csv_path, low_memory=False)
            logger.info(f"Read {len(df)} rows from conditions.csv")
            
            # Column mapping
            df.columns = df.columns.str.upper()
            column_mapping = {
                'START': 'start_date',
                'STOP': 'stop_date',
                'PATIENT': 'patient_id',
                'ENCOUNTER': 'encounter_id',
                'SYSTEM': 'system',
                'CODE': 'code',
                'DESCRIPTION': 'description'
            }
            
            df = df.rename(columns=column_mapping)
            
            # Convert dates
            df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')
            df['stop_date'] = pd.to_datetime(df['stop_date'], errors='coerce')
            
            # Validate and clean
            df = self.validate_and_clean_data(df, 'conditions')
            
            # Keep only expected columns
            expected_columns = list(column_mapping.values())
            df = df[[col for col in expected_columns if col in df.columns]]
            
            # Truncate and load
            if self.truncate_table('conditions'):
                loaded_rows = self.load_with_batch_processing(df, 'conditions')
                logger.info(f"Successfully loaded {loaded_rows} conditions")
                return loaded_rows
            
        except Exception as e:
            logger.error(f"Failed to import conditions: {e}")
            self.stats['errors'].append(f"conditions: {str(e)}")
            return 0
    
    def import_medications(self):
        """Import medications"""
        csv_path = os.path.join(self.csv_dir, 'medications.csv')
        
        try:
            logger.info("Loading medications.csv...")
            df = pd.read_csv(csv_path, low_memory=False)
            logger.info(f"Read {len(df)} rows from medications.csv")
            
            # Column mapping
            df.columns = df.columns.str.upper()
            column_mapping = {
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
            
            df = df.rename(columns=column_mapping)
            
            # Convert dates
            df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')
            df['stop_date'] = pd.to_datetime(df['stop_date'], errors='coerce')
            
            # Convert numeric columns
            numeric_columns = ['base_cost', 'payer_coverage', 'dispenses', 'total_cost']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Validate and clean
            df = self.validate_and_clean_data(df, 'medications')
            
            # Keep only expected columns
            expected_columns = list(column_mapping.values())
            df = df[[col for col in expected_columns if col in df.columns]]
            
            # Truncate and load
            if self.truncate_table('medications'):
                loaded_rows = self.load_with_batch_processing(df, 'medications')
                logger.info(f"Successfully loaded {loaded_rows} medications")
                return loaded_rows
            
        except Exception as e:
            logger.error(f"Failed to import medications: {e}")
            self.stats['errors'].append(f"medications: {str(e)}")
            return 0
    
    def validate_referential_integrity(self):
        """Basic referential integrity validation"""
        logger.info("Validating referential integrity...")
        
        try:
            with self.engine.connect() as conn:
                # Check key relationships
                checks = [
                    ("providers", "organization_id", "organizations", "id"),
                    ("encounters", "patient_id", "patients", "id"),
                    ("encounters", "provider_id", "providers", "id"),
                    ("encounters", "organization_id", "organizations", "id"),
                    ("conditions", "patient_id", "patients", "id"),
                    ("conditions", "encounter_id", "encounters", "id"),
                    ("medications", "patient_id", "patients", "id"),
                    ("medications", "encounter_id", "encounters", "id")
                ]
                
                violations = 0
                for child_table, child_col, parent_table, parent_col in checks:
                    try:
                        query = text(f"""
                            SELECT COUNT(*) 
                            FROM clinical_data.{child_table} c
                            LEFT JOIN clinical_data.{parent_table} p ON c.{child_col} = p.{parent_col}
                            WHERE c.{child_col} IS NOT NULL AND p.{parent_col} IS NULL
                        """)
                        
                        result = conn.execute(query)
                        violation_count = result.scalar()
                        
                        if violation_count > 0:
                            violations += violation_count
                            logger.warning(f"Found {violation_count} orphaned records in {child_table}.{child_col}")
                        else:
                            logger.info(f"✓ {child_table}.{child_col} -> {parent_table}.{parent_col}: OK")
                    
                    except Exception as e:
                        logger.warning(f"Could not validate {child_table}.{child_col}: {e}")
                
                logger.info(f"Referential integrity check complete. Total violations: {violations}")
                return violations == 0
        
        except Exception as e:
            logger.error(f"Error during integrity validation: {e}")
            return False
    
    def generate_summary(self):
        """Generate loading summary"""
        try:
            with self.engine.connect() as conn:
                tables = ['patients', 'organizations', 'providers', 'payers', 'encounters', 'conditions', 'medications']
                
                logger.info("=" * 60)
                logger.info("DATA LOADING SUMMARY")
                logger.info("=" * 60)
                
                total_records = 0
                for table in tables:
                    try:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM clinical_data.{table}"))
                        count = result.scalar()
                        total_records += count
                        logger.info(f"{table.upper():15}: {count:,} records")
                    except Exception as e:
                        logger.error(f"{table.upper():15}: Error - {e}")
                
                logger.info("=" * 60)
                logger.info(f"TOTAL RECORDS: {total_records:,}")
                logger.info(f"ERRORS: {len(self.stats['errors'])}")
                logger.info(f"WARNINGS: {len(self.stats['warnings'])}")
                
                if self.stats['errors']:
                    logger.info("\nERRORS:")
                    for error in self.stats['errors']:
                        logger.error(f"  - {error}")
                
                logger.info("=" * 60)
        
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
    
    def load_all_data(self):
        """Load all data with proper dependency order"""
        self.stats['start_time'] = datetime.now()
        logger.info("Starting enhanced data loading process...")
        
        # Load in dependency order
        loading_functions = [
            ('organizations', self.import_organizations),
            ('payers', self.import_payers),
            ('patients', self.import_patients),
            ('providers', self.import_providers),
            ('encounters', self.import_encounters),
            ('conditions', self.import_conditions),
            ('medications', self.import_medications)
        ]
        
        for table_name, load_func in loading_functions:
            logger.info(f"\n--- Loading {table_name} ---")
            rows_loaded = load_func()
            if rows_loaded > 0:
                self.stats['tables_loaded'] += 1
                self.stats['total_rows'] += rows_loaded
        
        # Validate integrity
        logger.info("\n--- Validating Data Integrity ---")
        integrity_ok = self.validate_referential_integrity()
        
        # Generate summary
        self.generate_summary()
        
        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        logger.info(f"\nLoading completed in {duration:.1f} seconds")
        logger.info(f"Tables loaded: {self.stats['tables_loaded']}")
        logger.info(f"Total rows: {self.stats['total_rows']:,}")
        
        return len(self.stats['errors']) == 0

def main():
    """Main execution function"""
    loader = SimpleEnhancedLoader()
    success = loader.load_all_data()
    return success

if __name__ == "__main__":
    main()