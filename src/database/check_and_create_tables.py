#!/usr/bin/env python3
"""
Check and create missing tables for enhanced data
"""

import os
import sys
import psycopg2
import logging

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.utils.env_loader import load_env_file

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection using environment variables"""
    try:
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

def check_table_exists(conn, table_name):
    """Check if a table exists"""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'clinical_data' 
                    AND table_name = %s
                );
            """, (table_name,))
            return cur.fetchone()[0]
    except Exception as e:
        logger.error(f"Error checking table {table_name}: {e}")
        return False

def create_immunizations_table(conn):
    """Create immunizations table"""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS clinical_data.immunizations (
                    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
                    date DATE NOT NULL,
                    patient_id UUID NOT NULL,
                    encounter_id UUID,
                    code VARCHAR(20) NOT NULL,
                    description TEXT NOT NULL,
                    base_cost DECIMAL(10, 2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            logger.info("Created immunizations table")
    except Exception as e:
        logger.error(f"Error creating immunizations table: {e}")
        conn.rollback()
        raise

def create_procedures_table(conn):
    """Create procedures table"""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS clinical_data.procedures (
                    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
                    date DATE NOT NULL,
                    patient_id UUID NOT NULL,
                    encounter_id UUID,
                    system VARCHAR(50),
                    code VARCHAR(20) NOT NULL,
                    description TEXT NOT NULL,
                    base_cost DECIMAL(10, 2),
                    reason_code VARCHAR(20),
                    reason_description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            logger.info("Created procedures table")
    except Exception as e:
        logger.error(f"Error creating procedures table: {e}")
        conn.rollback()
        raise

def main():
    """Main function to check and create tables"""
    logger.info("Checking and creating missing tables...")
    
    try:
        conn = get_db_connection()
        logger.info("Connected to database successfully")
        
        # Check and create immunizations table
        if not check_table_exists(conn, 'immunizations'):
            logger.info("Immunizations table does not exist, creating...")
            create_immunizations_table(conn)
        else:
            logger.info("Immunizations table already exists")
        
        # Check and create procedures table
        if not check_table_exists(conn, 'procedures'):
            logger.info("Procedures table does not exist, creating...")
            create_procedures_table(conn)
        else:
            logger.info("Procedures table already exists")
        
        # List all tables in clinical_data schema
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'clinical_data'
                ORDER BY table_name;
            """)
            tables = cur.fetchall()
            logger.info("Tables in clinical_data schema:")
            for table in tables:
                logger.info(f"  - {table[0]}")
        
        logger.info("Table check and creation completed successfully!")
        
    except Exception as e:
        logger.error(f"Table check and creation failed: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    main()