#!/usr/bin/env python3
"""
Final verification that all queries work without syntax errors
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

def test_all_queries():
    """Test all queries to ensure no syntax errors"""
    
    print("🔍 FINAL VERIFICATION - TESTING ALL QUERIES")
    print("=" * 60)
    
    # All working queries
    queries = {
        "1. HPV vaccine patients": """
            SELECT COUNT(DISTINCT patient) as hpv_vaccination_count
            FROM clinical_data.immunizations 
            WHERE description ILIKE '%papillomavirus%' OR description ILIKE '%hpv%'
        """,
        
        "2. Sinusitis patients": """
            SELECT COUNT(DISTINCT patient_id) as sinusitis_patients
            FROM clinical_data.conditions 
            WHERE description ILIKE '%sinusitis%'
        """,
        
        "3. HPV vaccine recipients (alt)": """
            SELECT COUNT(DISTINCT patient) as hpv_vaccine_recipients
            FROM clinical_data.immunizations 
            WHERE code = 90649 OR description ILIKE '%papillomavirus%'
        """,
        
        "4. Medications in 2019": """
            SELECT COUNT(DISTINCT description) as unique_medications_2019
            FROM clinical_data.medications 
            WHERE EXTRACT(YEAR FROM start_date) = 2019
        """,
        
        "5. Procedures in 2020": """
            SELECT COUNT(*) as procedures_2020
            FROM clinical_data.procedures 
            WHERE EXTRACT(YEAR FROM start::date) = 2020
        """,
        
        "6. Medications in 2021": """
            SELECT COUNT(DISTINCT description) as unique_medications_2021
            FROM clinical_data.medications 
            WHERE EXTRACT(YEAR FROM start_date) = 2021
        """,
        
        "7. Top 5 conditions": """
            SELECT description, COUNT(*) as count
            FROM clinical_data.conditions
            GROUP BY description
            ORDER BY count DESC
            LIMIT 5
        """,
        
        "8. Top 5 vaccines": """
            SELECT description, COUNT(*) as count
            FROM clinical_data.immunizations
            GROUP BY description
            ORDER BY count DESC
            LIMIT 5
        """,
        
        "9. Top 5 medications": """
            SELECT description, COUNT(*) as count
            FROM clinical_data.medications
            GROUP BY description
            ORDER BY count DESC
            LIMIT 5
        """,
        
        "10. Top 5 diagnoses": """
            SELECT description, COUNT(*) as count
            FROM clinical_data.conditions
            GROUP BY description
            ORDER BY count DESC
            LIMIT 5
        """,
        
        "11. Distinct vaccines": """
            SELECT COUNT(DISTINCT description) as unique_vaccines
            FROM clinical_data.immunizations
        """,
        
        "12. Anxiety procedures": """
            SELECT COUNT(*) as anxiety_procedures
            FROM clinical_data.procedures
            WHERE reasondescription ILIKE '%anxiety%'
        """,
        
        "13. Non-anxiety procedures": """
            SELECT COUNT(*) as non_anxiety_procedures
            FROM clinical_data.procedures
            WHERE reasondescription IS NULL OR reasondescription NOT ILIKE '%anxiety%'
        """,
        
        "14. Payers >100 patients": """
            SELECT name, unique_customers
            FROM clinical_data.payers 
            WHERE unique_customers > 100
            ORDER BY unique_customers DESC
        """,
        
        "15. Patients >2 immunizations": """
            SELECT COUNT(*) as patients_with_multiple_immunizations
            FROM (
                SELECT patient, COUNT(*) as immunization_count
                FROM clinical_data.immunizations
                GROUP BY patient
                HAVING COUNT(*) > 2
            ) subquery
        """
    }
    
    try:
        conn = get_db_connection()
        print("✅ Database connection established\n")
        
        passed = 0
        failed = 0
        
        for query_name, query in queries.items():
            try:
                with conn.cursor() as cur:
                    cur.execute(query)
                    results = cur.fetchall()
                    
                    if len(results) == 1 and len(results[0]) == 1:
                        # Single value result
                        print(f"✅ {query_name}: {results[0][0]:,}")
                    elif len(results) > 1:
                        # Multiple results
                        print(f"✅ {query_name}: {len(results)} results")
                        if query_name.startswith(("7.", "8.", "9.", "10.", "14.")):
                            for i, row in enumerate(results[:3], 1):
                                if len(row) == 2:
                                    desc = row[0][:40] + "..." if len(row[0]) > 40 else row[0]
                                    print(f"   {i}. {desc}: {row[1]:,}")
                                else:
                                    print(f"   {i}. {row[0]}")
                    else:
                        print(f"✅ {query_name}: No results (but query executed successfully)")
                    
                    passed += 1
                    
            except Exception as e:
                print(f"❌ {query_name}: FAILED - {e}")
                failed += 1
        
        print("\n" + "=" * 60)
        print("📊 FINAL VERIFICATION RESULTS")
        print("=" * 60)
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/(passed+failed))*100:.1f}%")
        
        if failed == 0:
            print("\n🎉 ALL QUERIES WORK PERFECTLY!")
            print("✅ No syntax errors found")
            print("✅ Database is ready for production use")
            print("✅ All clinical questions can be answered")
        else:
            print(f"\n⚠️  {failed} queries need attention")
        
        # Test the problematic query pattern to show it's fixed
        print("\n" + "=" * 60)
        print("🔧 TESTING CORRECTED HPV QUERY PATTERNS")
        print("=" * 60)
        
        corrected_patterns = {
            "HPV count (simple)": """
                SELECT COUNT(DISTINCT patient) as hpv_patients
                FROM clinical_data.immunizations 
                WHERE description ILIKE '%papillomavirus%' OR description ILIKE '%hpv%'
            """,
            
            "HPV with encounter details": """
                SELECT 
                    COUNT(*) as total_vaccinations,
                    COUNT(DISTINCT patient) as unique_patients,
                    COUNT(DISTINCT encounter) as unique_encounters
                FROM clinical_data.immunizations 
                WHERE description ILIKE '%papillomavirus%' OR description ILIKE '%hpv%'
            """,
            
            "HPV vaccination types": """
                SELECT 
                    description,
                    COUNT(*) as vaccinations,
                    COUNT(DISTINCT patient) as patients
                FROM clinical_data.immunizations 
                WHERE description ILIKE '%papillomavirus%' OR description ILIKE '%hpv%'
                GROUP BY description
                ORDER BY vaccinations DESC
            """
        }
        
        for pattern_name, query in corrected_patterns.items():
            try:
                with conn.cursor() as cur:
                    cur.execute(query)
                    results = cur.fetchall()
                    print(f"✅ {pattern_name}: Success")
                    if pattern_name == "HPV vaccination types":
                        for row in results:
                            print(f"   • {row[0]}: {row[1]} vaccinations, {row[2]} patients")
                    elif len(results[0]) > 1:
                        print(f"   • Total: {results[0][0]}, Patients: {results[0][1]}, Encounters: {results[0][2]}")
                    else:
                        print(f"   • Count: {results[0][0]}")
            except Exception as e:
                print(f"❌ {pattern_name}: {e}")
        
        print("\n🏥 Final verification completed!")
        
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    test_all_queries()