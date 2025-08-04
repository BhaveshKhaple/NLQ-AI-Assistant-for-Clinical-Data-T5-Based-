#!/usr/bin/env python3
"""
Sample detailed queries to showcase the data
"""

import os
import sys
import psycopg2

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.utils.env_loader import load_env_file

def get_db_connection():
    """Get database connection using environment variables"""
    load_env_file()
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'medical'),
        user=os.getenv('DB_USERNAME', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'Pass@123')
    )
    return conn

def run_sample_queries():
    """Run sample queries to showcase the data"""
    
    print("🔍 SAMPLE DETAILED QUERY RESULTS")
    print("=" * 60)
    
    conn = get_db_connection()
    
    # Sample 1: HPV vaccine details
    print("\n1. HPV VACCINE DETAILS:")
    print("-" * 30)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT description, COUNT(*) as count
            FROM clinical_data.immunizations 
            WHERE description ILIKE '%papillomavirus%' OR description ILIKE '%hpv%'
            GROUP BY description
            ORDER BY count DESC;
        """)
        results = cur.fetchall()
        for desc, count in results:
            print(f"   • {desc}: {count} administrations")
    
    # Sample 2: Sinusitis conditions
    print("\n2. SINUSITIS CONDITIONS:")
    print("-" * 30)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT description, COUNT(*) as count
            FROM clinical_data.conditions 
            WHERE description ILIKE '%sinusitis%'
            GROUP BY description
            ORDER BY count DESC;
        """)
        results = cur.fetchall()
        for desc, count in results:
            print(f"   • {desc}: {count} cases")
    
    # Sample 3: 2021 medications sample
    print("\n3. SAMPLE 2021 MEDICATIONS:")
    print("-" * 30)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT description, COUNT(*) as prescription_count
            FROM clinical_data.medications 
            WHERE EXTRACT(YEAR FROM start_date) = 2021
            GROUP BY description
            ORDER BY prescription_count DESC
            LIMIT 8;
        """)
        results = cur.fetchall()
        for desc, count in results:
            print(f"   • {desc[:50]}{'...' if len(desc) > 50 else ''}: {count} prescriptions")
    
    # Sample 4: Anxiety procedures
    print("\n4. ANXIETY-RELATED PROCEDURES:")
    print("-" * 30)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT p.description, p.reasondescription, COUNT(*) as procedure_count
            FROM clinical_data.procedures p
            WHERE p.reasondescription ILIKE '%anxiety%'
            GROUP BY p.description, p.reasondescription
            ORDER BY procedure_count DESC;
        """)
        results = cur.fetchall()
        for desc, reason, count in results:
            print(f"   • {desc}: {count} procedures")
            print(f"     Reason: {reason}")
    
    # Sample 5: Payer details
    print("\n5. MAJOR INSURANCE PAYERS:")
    print("-" * 30)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT name, unique_customers, amount_covered, revenue
            FROM clinical_data.payers 
            WHERE unique_customers > 100
            ORDER BY unique_customers DESC;
        """)
        results = cur.fetchall()
        for name, customers, covered, revenue in results:
            print(f"   • {name}:")
            print(f"     Patients: {customers:,}")
            print(f"     Amount Covered: ${covered:,.2f}")
            print(f"     Revenue: ${revenue:,.2f}")
    
    # Sample 6: Vaccine diversity
    print("\n6. VACCINE TYPES AVAILABLE:")
    print("-" * 30)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT description, COUNT(*) as administrations
            FROM clinical_data.immunizations
            GROUP BY description
            ORDER BY administrations DESC
            LIMIT 10;
        """)
        results = cur.fetchall()
        for desc, count in results:
            print(f"   • {desc[:45]}{'...' if len(desc) > 45 else ''}: {count}")
    
    conn.close()
    print("\n✅ Sample queries completed successfully!")

if __name__ == "__main__":
    run_sample_queries()