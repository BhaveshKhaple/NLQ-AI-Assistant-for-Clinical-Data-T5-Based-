#!/usr/bin/env python3
"""
Comprehensive test of all clinical questions
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

def run_query(conn, query):
    """Run a single query and return results"""
    try:
        conn.rollback()  # Reset any failed transaction
        with conn.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()
            return results
    except Exception as e:
        logger.error(f"Error running query: {e}")
        conn.rollback()
        return None

def test_clinical_questions():
    """Test all clinical questions"""
    
    print("=" * 80)
    print("🏥 COMPREHENSIVE CLINICAL QUESTIONS TEST")
    print("=" * 80)
    
    try:
        conn = get_db_connection()
        print("✅ Database connection established")
        print()
        
        # Test each question
        questions = [
            {
                "id": 1,
                "question": "How many patients received an HPV vaccine?",
                "query": """
                    SELECT COUNT(DISTINCT patient) as hpv_vaccine_patients
                    FROM clinical_data.immunizations 
                    WHERE description ILIKE '%papillomavirus%' OR description ILIKE '%hpv%';
                """,
                "expected_type": "count"
            },
            {
                "id": 2,
                "question": "How many patients were diagnosed with sinusitis?",
                "query": """
                    SELECT COUNT(DISTINCT patient_id) as sinusitis_patients
                    FROM clinical_data.conditions 
                    WHERE description ILIKE '%sinusitis%';
                """,
                "expected_type": "count"
            },
            {
                "id": 3,
                "question": "How many patients received vaccine - HPV?",
                "query": """
                    SELECT COUNT(DISTINCT patient) as hpv_vaccine_recipients
                    FROM clinical_data.immunizations 
                    WHERE code = 90649 OR description ILIKE '%papillomavirus%';
                """,
                "expected_type": "count"
            },
            {
                "id": 4,
                "question": "List all medications prescribed in 2019",
                "query": """
                    SELECT description as medication_name, COUNT(*) as prescription_count
                    FROM clinical_data.medications 
                    WHERE EXTRACT(YEAR FROM start_date) = 2019
                    GROUP BY description
                    ORDER BY prescription_count DESC
                    LIMIT 10;
                """,
                "expected_type": "list"
            },
            {
                "id": 5,
                "question": "How many procedures were done in 2020?",
                "query": """
                    SELECT COUNT(*) as procedures_2020
                    FROM clinical_data.procedures 
                    WHERE EXTRACT(YEAR FROM start::date) = 2020;
                """,
                "expected_type": "count"
            },
            {
                "id": 6,
                "question": "Show all medications prescribed in 2021",
                "query": """
                    SELECT description as medication_name, COUNT(*) as prescription_count
                    FROM clinical_data.medications 
                    WHERE EXTRACT(YEAR FROM start_date) = 2021
                    GROUP BY description
                    ORDER BY prescription_count DESC
                    LIMIT 10;
                """,
                "expected_type": "list"
            },
            {
                "id": 7,
                "question": "Top 5 most common conditions?",
                "query": """
                    SELECT description as condition_name, COUNT(*) as occurrence_count
                    FROM clinical_data.conditions
                    GROUP BY description
                    ORDER BY occurrence_count DESC
                    LIMIT 5;
                """,
                "expected_type": "list"
            },
            {
                "id": 8,
                "question": "Most frequent vaccines given?",
                "query": """
                    SELECT description as vaccine_name, COUNT(*) as administration_count
                    FROM clinical_data.immunizations
                    GROUP BY description
                    ORDER BY administration_count DESC
                    LIMIT 5;
                """,
                "expected_type": "list"
            },
            {
                "id": 9,
                "question": "What are the top 5 most common medications prescribed?",
                "query": """
                    SELECT description as medication_name, COUNT(*) as prescription_count
                    FROM clinical_data.medications
                    GROUP BY description
                    ORDER BY prescription_count DESC
                    LIMIT 5;
                """,
                "expected_type": "list"
            },
            {
                "id": 10,
                "question": "Top 5 most frequent diagnoses in conditions",
                "query": """
                    SELECT description as diagnosis, COUNT(*) as frequency
                    FROM clinical_data.conditions
                    GROUP BY description
                    ORDER BY frequency DESC
                    LIMIT 5;
                """,
                "expected_type": "list"
            },
            {
                "id": 11,
                "question": "List all distinct vaccines given to patients",
                "query": """
                    SELECT DISTINCT description as vaccine_name
                    FROM clinical_data.immunizations
                    ORDER BY vaccine_name
                    LIMIT 10;
                """,
                "expected_type": "list"
            },
            {
                "id": 12,
                "question": "List all procedures involving anxiety",
                "query": """
                    SELECT p.description as procedure_name, COUNT(*) as procedure_count
                    FROM clinical_data.procedures p
                    WHERE p.reasondescription ILIKE '%anxiety%'
                    GROUP BY p.description
                    ORDER BY procedure_count DESC
                    LIMIT 10;
                """,
                "expected_type": "list"
            },
            {
                "id": 13,
                "question": "List all procedures not involving anxiety",
                "query": """
                    SELECT p.description as procedure_name, COUNT(*) as procedure_count
                    FROM clinical_data.procedures p
                    WHERE p.reasondescription IS NULL OR p.reasondescription NOT ILIKE '%anxiety%'
                    GROUP BY p.description
                    ORDER BY procedure_count DESC
                    LIMIT 10;
                """,
                "expected_type": "list"
            },
            {
                "id": 14,
                "question": "Which payers covered more than 100 patients?",
                "query": """
                    SELECT name, unique_customers
                    FROM clinical_data.payers 
                    WHERE unique_customers > 100
                    ORDER BY unique_customers DESC;
                """,
                "expected_type": "list"
            },
            {
                "id": 15,
                "question": "How many patients received more than 2 immunizations?",
                "query": """
                    SELECT COUNT(*) as patients_with_multiple_immunizations
                    FROM (
                        SELECT patient, COUNT(*) as immunization_count
                        FROM clinical_data.immunizations
                        GROUP BY patient
                        HAVING COUNT(*) > 2
                    ) subquery;
                """,
                "expected_type": "count"
            }
        ]
        
        # Run each test
        passed_tests = 0
        total_tests = len(questions)
        
        for test in questions:
            print(f"🔍 Question {test['id']}: {test['question']}")
            print("-" * 60)
            
            results = run_query(conn, test['query'])
            
            if results is not None:
                if test['expected_type'] == 'count':
                    if len(results) == 1 and len(results[0]) == 1:
                        count = results[0][0]
                        print(f"✅ ANSWER: {count:,}")
                        if count > 0:
                            passed_tests += 1
                            print("✅ TEST PASSED: Data found")
                        else:
                            print("⚠️  TEST WARNING: No data found")
                    else:
                        print("❌ TEST FAILED: Unexpected result format")
                        
                elif test['expected_type'] == 'list':
                    if len(results) > 0:
                        print(f"✅ ANSWER: Found {len(results)} results")
                        for i, row in enumerate(results[:5], 1):
                            if len(row) == 2:
                                print(f"   {i}. {row[0]} ({row[1]:,})")
                            else:
                                print(f"   {i}. {row[0]}")
                        if len(results) > 5:
                            print(f"   ... and {len(results) - 5} more")
                        passed_tests += 1
                        print("✅ TEST PASSED: Data found")
                    else:
                        print("❌ TEST FAILED: No results found")
            else:
                print("❌ TEST FAILED: Query error")
            
            print()
        
        # Summary
        print("=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed Tests: {passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! Database is ready for clinical questions.")
        else:
            print(f"⚠️  {total_tests - passed_tests} tests need attention.")
        
        # Additional verification queries
        print("\n" + "=" * 80)
        print("📈 DATABASE STATISTICS")
        print("=" * 80)
        
        stats_queries = {
            "Total Patients": "SELECT COUNT(*) FROM clinical_data.patients",
            "Total Encounters": "SELECT COUNT(*) FROM clinical_data.encounters",
            "Total Conditions": "SELECT COUNT(*) FROM clinical_data.conditions",
            "Total Medications": "SELECT COUNT(*) FROM clinical_data.medications",
            "Total Immunizations": "SELECT COUNT(*) FROM clinical_data.immunizations",
            "Total Procedures": "SELECT COUNT(*) FROM clinical_data.procedures",
            "Total Payers": "SELECT COUNT(*) FROM clinical_data.payers",
            "Date Range": """
                SELECT 
                    MIN(start_date) as earliest_date,
                    MAX(start_date) as latest_date
                FROM clinical_data.medications
            """
        }
        
        for stat_name, query in stats_queries.items():
            results = run_query(conn, query)
            if results:
                if stat_name == "Date Range":
                    print(f"{stat_name}: {results[0][0]} to {results[0][1]}")
                else:
                    print(f"{stat_name}: {results[0][0]:,}")
        
        print("\n🏥 Clinical database testing completed!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    test_clinical_questions()