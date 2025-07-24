#!/usr/bin/env python3
"""
Simple Synthea Data Import - Direct CSV to PostgreSQL
"""

import os
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
import logging
from urllib.parse import quote_plus

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Simple import of key tables"""
    
    # Database configuration
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'medical',
        'user': 'postgres',
        'password': 'Pass@123'
    }
    
    # Create connection
    password_encoded = quote_plus(db_config['password'])
    connection_string = (
        f"postgresql://{db_config['user']}:{password_encoded}"
        f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    )
    engine = create_engine(connection_string)
    
    # CSV directory
    csv_dir = r'd:\projects\healthca\output\csv'
    
    # Import key tables with minimal processing
    tables_to_import = [
        ('patients.csv', 'patients'),
        ('encounters.csv', 'encounters'),
        ('conditions.csv', 'conditions'),
        ('medications.csv', 'medications'),
        ('observations.csv', 'observations')
    ]
    
    for csv_file, table_name in tables_to_import:
        csv_path = os.path.join(csv_dir, csv_file)
        
        if not os.path.exists(csv_path):
            logger.warning(f"File not found: {csv_path}")
            continue
            
        try:
            logger.info(f"Importing {csv_file}...")
            
            # Read CSV
            df = pd.read_csv(csv_path)
            logger.info(f"Read {len(df)} rows from {csv_file}")
            
            # Clean column names
            df.columns = df.columns.str.lower().str.replace(' ', '_')
            
            # Basic data type conversions
            if table_name == 'patients':
                # Convert dates
                if 'birthdate' in df.columns:
                    df['birthdate'] = pd.to_datetime(df['birthdate'], errors='coerce')
                if 'deathdate' in df.columns:
                    df['deathdate'] = pd.to_datetime(df['deathdate'], errors='coerce')
                    
            elif table_name == 'encounters':
                # Convert timestamps
                if 'start' in df.columns:
                    df['start'] = pd.to_datetime(df['start'], errors='coerce')
                if 'stop' in df.columns:
                    df['stop'] = pd.to_datetime(df['stop'], errors='coerce')
                    
            elif table_name == 'conditions':
                # Convert dates
                if 'start' in df.columns:
                    df['start'] = pd.to_datetime(df['start'], errors='coerce')
                if 'stop' in df.columns:
                    df['stop'] = pd.to_datetime(df['stop'], errors='coerce')
                    
            elif table_name == 'medications':
                # Convert dates
                if 'start' in df.columns:
                    df['start'] = pd.to_datetime(df['start'], errors='coerce')
                if 'stop' in df.columns:
                    df['stop'] = pd.to_datetime(df['stop'], errors='coerce')
                    
            elif table_name == 'observations':
                # Convert dates
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'], errors='coerce')
            
            # Replace NaN with None
            df = df.where(pd.notnull(df), None)
            
            # Import to database
            df.to_sql(
                table_name,
                engine,
                schema='clinical_data',
                if_exists='replace',  # Replace existing data
                index=False,
                method='multi',
                chunksize=1000
            )
            
            logger.info(f"Successfully imported {len(df)} rows into clinical_data.{table_name}")
            
        except Exception as e:
            logger.error(f"Failed to import {csv_file}: {e}")
            continue
    
    # Generate summary
    try:
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()
        
        logger.info("=== IMPORT SUMMARY ===")
        for _, table_name in tables_to_import:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM clinical_data.{table_name}")
                count = cursor.fetchone()[0]
                logger.info(f"{table_name.upper()}: {count:,} records")
            except:
                logger.info(f"{table_name.upper()}: Table not found")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        logger.error(f"Failed to generate summary: {e}")
    
    logger.info("Import completed!")

if __name__ == "__main__":
    main()