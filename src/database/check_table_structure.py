#!/usr/bin/env python3
"""
Check the actual structure of database tables
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

def check_table_structure(conn, table_name):
    """Check the structure of a table"""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_schema = 'clinical_data' 
                AND table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            columns = cur.fetchall()
            
            logger.info(f"Structure of {table_name} table:")
            for col in columns:
                logger.info(f"  - {col[0]} ({col[1]}) - Nullable: {col[2]} - Default: {col[3]}")
            
            return columns
    except Exception as e:
        logger.error(f"Error checking table structure for {table_name}: {e}")
        return []

def main():
    """Main function to check table structures"""
    logger.info("Checking table structures...")
    
    try:
        conn = get_db_connection()
        logger.info("Connected to database successfully")
        
        # Check immunizations table structure
        check_table_structure(conn, 'immunizations')
        
        # Check procedures table structure
        check_table_structure(conn, 'procedures')
        
        # Check medications table structure
        check_table_structure(conn, 'medications')
        
        # Check conditions table structure
        check_table_structure(conn, 'conditions')
        
        # Check payers table structure
        check_table_structure(conn, 'payers')
        
        # Check a few rows from existing tables to understand the data
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM clinical_data.immunizations")
            count = cur.fetchone()[0]
            logger.info(f"Current immunizations count: {count}")
            
            if count > 0:
                cur.execute("SELECT * FROM clinical_data.immunizations LIMIT 3")
                rows = cur.fetchall()
                logger.info("Sample immunizations data:")
                for row in rows:
                    logger.info(f"  {row}")
        
        logger.info("Table structure check completed!")
        
    except Exception as e:
        logger.error(f"Table structure check failed: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    main()