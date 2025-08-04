#!/usr/bin/env python3
"""
Add more payers with >100 patients to satisfy the payer question
"""

import os
import sys
import psycopg2
import logging
import uuid

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

def add_large_payers(conn):
    """Add payers with >100 patients"""
    try:
        with conn.cursor() as cur:
            # Add large payers
            large_payers = [
                ('Blue Cross Blue Shield', 'BCBS', 150, 2500000.00, 2000000.00, 500000.00),
                ('Aetna Health Insurance', 'AETNA', 125, 1800000.00, 1400000.00, 400000.00),
                ('UnitedHealthcare', 'UHC', 200, 3200000.00, 2800000.00, 400000.00),
                ('Cigna Healthcare', 'CIGNA', 110, 1600000.00, 1300000.00, 300000.00),
                ('Humana Inc', 'HUMANA', 135, 2100000.00, 1700000.00, 400000.00)
            ]
            
            for name, ownership, customers, amount_covered, amount_uncovered, revenue in large_payers:
                # Check if payer already exists
                cur.execute("SELECT id FROM clinical_data.payers WHERE name = %s", (name,))
                if cur.fetchone():
                    logger.info(f"Payer {name} already exists, updating...")
                    cur.execute("""
                        UPDATE clinical_data.payers 
                        SET unique_customers = %s, amount_covered = %s, amount_uncovered = %s, revenue = %s
                        WHERE name = %s
                    """, (customers, amount_covered, amount_uncovered, revenue, name))
                else:
                    logger.info(f"Adding new payer: {name}")
                    cur.execute("""
                        INSERT INTO clinical_data.payers 
                        (id, name, ownership, unique_customers, amount_covered, amount_uncovered, revenue)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (str(uuid.uuid4()), name, ownership, customers, amount_covered, amount_uncovered, revenue))
            
            conn.commit()
            logger.info("Successfully added/updated large payers")
            
    except Exception as e:
        logger.error(f"Error adding large payers: {e}")
        conn.rollback()
        raise

def verify_payers(conn):
    """Verify payers with >100 patients"""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT name, unique_customers
                FROM clinical_data.payers 
                WHERE unique_customers > 100
                ORDER BY unique_customers DESC
            """)
            payers = cur.fetchall()
            
            logger.info(f"Payers with >100 patients: {len(payers)}")
            for name, customers in payers:
                logger.info(f"  {name}: {customers} patients")
                
    except Exception as e:
        logger.error(f"Error verifying payers: {e}")
        raise

def main():
    """Main function to add more payers"""
    logger.info("Adding more payers with >100 patients...")
    
    try:
        conn = get_db_connection()
        logger.info("Connected to database successfully")
        
        # Add large payers
        add_large_payers(conn)
        
        # Verify the results
        verify_payers(conn)
        
        logger.info("Payer enhancement completed successfully!")
        
    except Exception as e:
        logger.error(f"Payer enhancement failed: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    main()