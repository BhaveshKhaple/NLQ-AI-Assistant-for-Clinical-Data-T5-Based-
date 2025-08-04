#!/usr/bin/env python3
"""
Run test queries to verify all clinical questions can be answered
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

def run_query(conn, query_name, query):
    """Run a single query and return results"""
    try:
        conn.rollback()  # Reset any failed transaction
        with conn.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()
            return results
    except Exception as e:
        logger.error(f"Error running query '{query_name}': {e}")
        conn.rollback()  # Reset failed transaction
        return None

def main():
    """Main function to run test queries"""
    logger.info("Running test queries to verify clinical data...")
    
    try:
        conn = get_db_connection()
        logger.info("Connected to database successfully")
        
        # Define test queries
        queries = {
            "1. HPV vaccine patients": """
                SELECT COUNT(DISTINCT patient) as hpv_vaccine_patients
                FROM clinical_data.immunizations 
                WHERE description ILIKE '%papillomavirus%' OR description ILIKE '%hpv%';
            """,
            
            "2. Sinusitis patients": """
                SELECT COUNT(DISTINCT patient_id) as sinusitis_patients
                FROM clinical_data.conditions 
                WHERE description ILIKE '%sinusitis%';
            """,
            
            "3. HPV vaccine recipients (alt)": """
                SELECT COUNT(DISTINCT patient) as hpv_vaccine_recipients
                FROM clinical_data.immunizations 
                WHERE code = 90649 OR description ILIKE '%papillomavirus%';
            """,
            
            "4. Medications prescribed in 2019": """
                SELECT COUNT(DISTINCT description) as unique_medications_2019
                FROM clinical_data.medications 
                WHERE EXTRACT(YEAR FROM start_date) = 2019;
            """,
            
            "5. Procedures done in 2020": """
                SELECT COUNT(*) as procedures_2020
                FROM clinical_data.procedures 
                WHERE EXTRACT(YEAR FROM start::date) = 2020;
            """,
            
            "6. Medications prescribed in 2021": """
                SELECT COUNT(DISTINCT description) as unique_medications_2021
                FROM clinical_data.medications 
                WHERE EXTRACT(YEAR FROM start_date) = 2021;
            """,
            
            "7. Top 5 most common conditions": """
                SELECT description as condition_name, COUNT(*) as occurrence_count
                FROM clinical_data.conditions
                GROUP BY description
                ORDER BY occurrence_count DESC
                LIMIT 5;
            """,
            
            "8. Most frequent vaccines given": """
                SELECT description as vaccine_name, COUNT(*) as administration_count
                FROM clinical_data.immunizations
                GROUP BY description
                ORDER BY administration_count DESC
                LIMIT 5;
            """,
            
            "9. Top 5 most common medications": """
                SELECT description as medication_name, COUNT(*) as prescription_count
                FROM clinical_data.medications
                GROUP BY description
                ORDER BY prescription_count DESC
                LIMIT 5;
            """,
            
            "10. Top 5 most frequent diagnoses": """
                SELECT description as diagnosis, COUNT(*) as frequency
                FROM clinical_data.conditions
                GROUP BY description
                ORDER BY frequency DESC
                LIMIT 5;
            """,
            
            "11. Distinct vaccines count": """
                SELECT COUNT(DISTINCT description) as unique_vaccines
                FROM clinical_data.immunizations;
            """,
            
            "12. Procedures involving anxiety": """
                SELECT COUNT(*) as anxiety_procedures
                FROM clinical_data.procedures p
                WHERE p.reasondescription ILIKE '%anxiety%';
            """,
            
            "13. Procedures not involving anxiety": """
                SELECT COUNT(*) as non_anxiety_procedures
                FROM clinical_data.procedures p
                WHERE p.reasondescription IS NULL OR p.reasondescription NOT ILIKE '%anxiety%';
            """,
            
            "14. Payers with >100 patients": """
                SELECT COUNT(*) as payers_over_100
                FROM clinical_data.payers 
                WHERE unique_customers > 100;
            """,
            
            "15. Patients with >2 immunizations": """
                SELECT COUNT(*) as patients_with_multiple_immunizations
                FROM (
                    SELECT patient, COUNT(*) as immunization_count
                    FROM clinical_data.immunizations
                    GROUP BY patient
                    HAVING COUNT(*) > 2
                ) subquery;
            """
        }
        
        # Run all queries
        logger.info("=" * 60)
        logger.info("CLINICAL DATA VERIFICATION RESULTS")
        logger.info("=" * 60)
        
        for query_name, query in queries.items():
            results = run_query(conn, query_name, query)
            if results is not None:
                if len(results) == 1 and len(results[0]) == 1:
                    # Single value result
                    logger.info(f"{query_name}: {results[0][0]}")
                else:
                    # Multiple results
                    logger.info(f"{query_name}:")
                    for row in results[:5]:  # Show top 5 results
                        logger.info(f"  {row}")
                    if len(results) > 5:
                        logger.info(f"  ... and {len(results) - 5} more")
            else:
                logger.error(f"{query_name}: FAILED")
            logger.info("-" * 40)
        
        # Additional summary statistics
        logger.info("SUMMARY STATISTICS:")
        summary_queries = {
            "Total patients": "SELECT COUNT(*) FROM clinical_data.patients",
            "Total encounters": "SELECT COUNT(*) FROM clinical_data.encounters", 
            "Total conditions": "SELECT COUNT(*) FROM clinical_data.conditions",
            "Total medications": "SELECT COUNT(*) FROM clinical_data.medications",
            "Total immunizations": "SELECT COUNT(*) FROM clinical_data.immunizations",
            "Total procedures": "SELECT COUNT(*) FROM clinical_data.procedures",
            "Total payers": "SELECT COUNT(*) FROM clinical_data.payers"
        }
        
        for stat_name, query in summary_queries.items():
            results = run_query(conn, stat_name, query)
            if results:
                logger.info(f"{stat_name}: {results[0][0]}")
        
        logger.info("=" * 60)
        logger.info("Test queries completed successfully!")
        
    except Exception as e:
        logger.error(f"Test queries failed: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    main()