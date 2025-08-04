#!/usr/bin/env python3
"""
Debug and fix the query issue
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

def get_correct_hpv_query():
    """Get the correct HPV vaccination query"""
    return """
        SELECT COUNT(DISTINCT patient) as hpv_vaccination_count
        FROM clinical_data.immunizations 
        WHERE description ILIKE '%papillomavirus%' OR description ILIKE '%hpv%'
    """

def get_alternative_hpv_queries():
    """Get alternative HPV queries that work with our schema"""
    return {
        "HPV patients by description": """
            SELECT COUNT(DISTINCT patient) as hpv_patients
            FROM clinical_data.immunizations 
            WHERE description ILIKE '%papillomavirus%' OR description ILIKE '%hpv%'
        """,
        
        "HPV patients by code": """
            SELECT COUNT(DISTINCT patient) as hpv_patients
            FROM clinical_data.immunizations 
            WHERE code = 90649
        """,
        
        "HPV vaccinations with details": """
            SELECT 
                description,
                COUNT(*) as vaccination_count,
                COUNT(DISTINCT patient) as unique_patients
            FROM clinical_data.immunizations 
            WHERE description ILIKE '%papillomavirus%' OR description ILIKE '%hpv%'
            GROUP BY description
            ORDER BY vaccination_count DESC
        """,
        
        "HPV patients with encounter info": """
            SELECT 
                i.patient,
                i.description,
                i.date,
                i.encounter
            FROM clinical_data.immunizations i
            WHERE i.description ILIKE '%papillomavirus%' OR i.description ILIKE '%hpv%'
            ORDER BY i.date DESC
            LIMIT 10
        """
    }

def main():
    """Main function to debug and fix query issues"""
    logger.info("Debugging query issues...")
    
    try:
        conn = get_db_connection()
        logger.info("Connected to database successfully")
        
        # Check if problematic table exists
        if check_table_exists(conn, 'clinical_dates'):
            logger.info("✅ clinical_dates table exists")
        else:
            logger.warning("❌ clinical_dates table does not exist")
        
        # Test the correct HPV query
        logger.info("Testing correct HPV vaccination query...")
        
        with conn.cursor() as cur:
            correct_query = get_correct_hpv_query()
            logger.info(f"Executing: {correct_query}")
            
            cur.execute(correct_query)
            result = cur.fetchone()
            logger.info(f"✅ HPV vaccination count: {result[0]}")
        
        # Test alternative queries
        logger.info("\nTesting alternative HPV queries...")
        alternative_queries = get_alternative_hpv_queries()
        
        for query_name, query in alternative_queries.items():
            try:
                logger.info(f"\n--- {query_name} ---")
                with conn.cursor() as cur:
                    cur.execute(query)
                    results = cur.fetchall()
                    
                    if query_name == "HPV vaccinations with details":
                        for row in results:
                            logger.info(f"  {row[0]}: {row[1]} vaccinations, {row[2]} patients")
                    elif query_name == "HPV patients with encounter info":
                        logger.info(f"  Found {len(results)} recent HPV vaccinations:")
                        for row in results[:5]:
                            logger.info(f"    Patient: {row[0][:8]}..., Vaccine: {row[1][:30]}..., Date: {row[2]}")
                    else:
                        logger.info(f"  Result: {results[0][0]}")
                        
            except Exception as e:
                logger.error(f"  ❌ Query failed: {e}")
        
        # Provide corrected queries for common scenarios
        logger.info("\n" + "="*60)
        logger.info("CORRECTED QUERIES FOR COMMON SCENARIOS")
        logger.info("="*60)
        
        corrected_queries = {
            "HPV vaccination count": """
                SELECT COUNT(DISTINCT patient) as hpv_vaccination_count
                FROM clinical_data.immunizations 
                WHERE description ILIKE '%papillomavirus%' OR description ILIKE '%hpv%'
            """,
            
            "HPV vaccinations by encounter": """
                SELECT 
                    COUNT(*) as total_hpv_vaccinations,
                    COUNT(DISTINCT patient) as unique_patients,
                    COUNT(DISTINCT encounter) as unique_encounters
                FROM clinical_data.immunizations 
                WHERE description ILIKE '%papillomavirus%' OR description ILIKE '%hpv%'
            """,
            
            "HPV vaccinations with patient demographics": """
                SELECT 
                    p.id as patient_id,
                    p.first_name,
                    p.last_name,
                    p.birthdate,
                    i.description as vaccine_type,
                    i.date as vaccination_date
                FROM clinical_data.patients p
                JOIN clinical_data.immunizations i ON p.id = i.patient
                WHERE i.description ILIKE '%papillomavirus%' OR i.description ILIKE '%hpv%'
                ORDER BY i.date DESC
                LIMIT 10
            """
        }
        
        for query_name, query in corrected_queries.items():
            logger.info(f"\n{query_name}:")
            logger.info(f"```sql{query}```")
        
        logger.info("\n✅ Query debugging completed successfully!")
        
    except Exception as e:
        logger.error(f"Debugging failed: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    main()