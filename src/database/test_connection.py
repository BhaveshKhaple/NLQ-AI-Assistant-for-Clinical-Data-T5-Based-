#!/usr/bin/env python3
"""
Test PostgreSQL database connection
"""

import psycopg2
import sys

def test_connection():
    """Test database connection with different password options"""
    
    # Try common default passwords
    passwords_to_try = ['Pass@123', 'admin', '123456', '', 'password']
    
    db_config_base = {
        'host': 'localhost',
        'port': 5432,
        'database': 'medical',
        'user': 'postgres'
    }
    
    for password in passwords_to_try:
        try:
            db_config = db_config_base.copy()
            db_config['password'] = password
            
            print(f"Trying password: {'(empty)' if password == '' else password}")
            
            connection = psycopg2.connect(**db_config)
            cursor = connection.cursor()
            
            # Test the connection
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            cursor.close()
            connection.close()
            
            print(f"✅ SUCCESS! Connected to PostgreSQL")
            print(f"Version: {version}")
            print(f"Working password: {'(empty)' if password == '' else password}")
            
            return password
            
        except psycopg2.OperationalError as e:
            print(f"❌ Failed with password '{password}': {e}")
            continue
        except Exception as e:
            print(f"❌ Unexpected error with password '{password}': {e}")
            continue
    
    print("❌ Could not connect with any common passwords")
    return None

if __name__ == "__main__":
    working_password = test_connection()
    if working_password is not None:
        print(f"\n🎉 Use password: '{working_password}' for database connections")
    else:
        print("\n💡 You may need to:")
        print("1. Check if PostgreSQL service is running")
        print("2. Reset the postgres user password")
        print("3. Check pg_hba.conf authentication settings")