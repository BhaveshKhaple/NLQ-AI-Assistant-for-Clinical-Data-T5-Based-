#!/usr/bin/env python3
"""
Enhanced Data Import Script for Clinical NLQ AI Assistant
Imports immunizations, procedures, and enhanced conditions/medications data
"""

import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import logging

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.utils.env_loader import load_env_file

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_data_import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection using environment variables"""
    try:
        # Load environment variables
        load_env_file()
        
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'medical'),
            user=os.getenv('DB_USERNAME', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'Pass@123')
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

def import_immunizations(conn, csv_path):
    """Import immunizations data"""
    logger.info("Importing immunizations data...")
    
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} immunization records")
        
        # Prepare data for insertion
        records = []
        for _, row in df.iterrows():
            records.append((
                row['DATE'],
                row['PATIENT'],
                row['ENCOUNTER'] if pd.notna(row['ENCOUNTER']) else None,
                int(row['CODE']) if pd.notna(row['CODE']) else None,
                row['DESCRIPTION'],
                float(row['BASE_COST']) if pd.notna(row['BASE_COST']) else None
            ))
        
        # Insert data
        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO clinical_data.immunizations 
                (date, patient, encounter, code, description, base_cost)
                VALUES %s
                ON CONFLICT DO NOTHING
                """,
                records,
                template=None,
                page_size=100
            )
            conn.commit()
            logger.info(f"Successfully imported {len(records)} immunization records")
            
    except Exception as e:
        logger.error(f"Error importing immunizations: {e}")
        conn.rollback()
        raise

def import_procedures(conn, csv_path):
    """Import procedures data"""
    logger.info("Importing procedures data...")
    
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} procedure records")
        
        # Prepare data for insertion
        records = []
        for _, row in df.iterrows():
            records.append((
                row['DATE'],
                None,  # stop date - not provided in our data
                row['PATIENT'],
                row['ENCOUNTER'] if pd.notna(row['ENCOUNTER']) else None,
                row['SYSTEM'] if pd.notna(row['SYSTEM']) else None,
                int(row['CODE']) if pd.notna(row['CODE']) else None,
                row['DESCRIPTION'],
                float(row['BASE_COST']) if pd.notna(row['BASE_COST']) else None,
                float(row['REASONCODE']) if pd.notna(row['REASONCODE']) else None,
                row['REASONDESCRIPTION'] if pd.notna(row['REASONDESCRIPTION']) else None
            ))
        
        # Insert data
        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO clinical_data.procedures 
                (start, stop, patient, encounter, system, code, description, base_cost, reasoncode, reasondescription)
                VALUES %s
                ON CONFLICT DO NOTHING
                """,
                records,
                template=None,
                page_size=100
            )
            conn.commit()
            logger.info(f"Successfully imported {len(records)} procedure records")
            
    except Exception as e:
        logger.error(f"Error importing procedures: {e}")
        conn.rollback()
        raise

def verify_data_import(conn):
    """Verify the imported data"""
    logger.info("Verifying imported data...")
    
    try:
        with conn.cursor() as cur:
            # Check immunizations
            cur.execute("SELECT COUNT(*) FROM clinical_data.immunizations")
            immunizations_count = cur.fetchone()[0]
            logger.info(f"Total immunizations in database: {immunizations_count}")
            
            # Check HPV vaccines specifically
            cur.execute("""
                SELECT COUNT(*) FROM clinical_data.immunizations 
                WHERE description ILIKE '%papillomavirus%' OR description ILIKE '%hpv%'
            """)
            hpv_count = cur.fetchone()[0]
            logger.info(f"HPV vaccines in database: {hpv_count}")
            
            # Check procedures
            cur.execute("SELECT COUNT(*) FROM clinical_data.procedures")
            procedures_count = cur.fetchone()[0]
            logger.info(f"Total procedures in database: {procedures_count}")
            
            # Check anxiety-related procedures
            cur.execute("""
                SELECT COUNT(*) FROM clinical_data.procedures 
                WHERE reasondescription ILIKE '%anxiety%'
            """)
            anxiety_procedures_count = cur.fetchone()[0]
            logger.info(f"Anxiety-related procedures in database: {anxiety_procedures_count}")
            
            # Check conditions
            cur.execute("SELECT COUNT(*) FROM clinical_data.conditions")
            conditions_count = cur.fetchone()[0]
            logger.info(f"Total conditions in database: {conditions_count}")
            
            # Check sinusitis conditions
            cur.execute("""
                SELECT COUNT(*) FROM clinical_data.conditions 
                WHERE description ILIKE '%sinusitis%'
            """)
            sinusitis_count = cur.fetchone()[0]
            logger.info(f"Sinusitis conditions in database: {sinusitis_count}")
            
            # Check medications
            cur.execute("SELECT COUNT(*) FROM clinical_data.medications")
            medications_count = cur.fetchone()[0]
            logger.info(f"Total medications in database: {medications_count}")
            
            # Check 2019 medications
            cur.execute("""
                SELECT COUNT(*) FROM clinical_data.medications 
                WHERE EXTRACT(YEAR FROM start_date) = 2019
            """)
            meds_2019_count = cur.fetchone()[0]
            logger.info(f"2019 medications in database: {meds_2019_count}")
            
            # Check 2020 medications
            cur.execute("""
                SELECT COUNT(*) FROM clinical_data.medications 
                WHERE EXTRACT(YEAR FROM start_date) = 2020
            """)
            meds_2020_count = cur.fetchone()[0]
            logger.info(f"2020 medications in database: {meds_2020_count}")
            
            # Check 2021 medications
            cur.execute("""
                SELECT COUNT(*) FROM clinical_data.medications 
                WHERE EXTRACT(YEAR FROM start_date) = 2021
            """)
            meds_2021_count = cur.fetchone()[0]
            logger.info(f"2021 medications in database: {meds_2021_count}")
            
            # Check payers with more than 100 patients
            cur.execute("""
                SELECT name, unique_customers
                FROM clinical_data.payers 
                WHERE unique_customers > 100
                ORDER BY unique_customers DESC
            """)
            payers_results = cur.fetchall()
            logger.info(f"Payers with >100 patients: {len(payers_results)}")
            for payer_name, count in payers_results:
                logger.info(f"  {payer_name}: {count} patients")
                
    except Exception as e:
        logger.error(f"Error verifying data: {e}")
        raise

def main():
    """Main function to import enhanced data"""
    logger.info("Starting enhanced data import...")
    
    try:
        # Get database connection
        conn = get_db_connection()
        logger.info("Connected to database successfully")
        
        # Define CSV file paths
        csv_dir = os.path.join(project_root, 'output', 'csv')
        immunizations_csv = os.path.join(csv_dir, 'immunizations.csv')
        procedures_csv = os.path.join(csv_dir, 'procedures.csv')
        
        # Import immunizations
        if os.path.exists(immunizations_csv):
            import_immunizations(conn, immunizations_csv)
        else:
            logger.warning(f"Immunizations CSV not found: {immunizations_csv}")
        
        # Import procedures
        if os.path.exists(procedures_csv):
            import_procedures(conn, procedures_csv)
        else:
            logger.warning(f"Procedures CSV not found: {procedures_csv}")
        
        # Verify the import
        verify_data_import(conn)
        
        logger.info("Enhanced data import completed successfully!")
        
    except Exception as e:
        logger.error(f"Enhanced data import failed: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    main()