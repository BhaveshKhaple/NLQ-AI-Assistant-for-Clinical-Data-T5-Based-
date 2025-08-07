#!/usr/bin/env python3
"""
Test database connection and diagnose connection issues
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
src_path = str(Path(__file__).parent / 'src')
sys.path.insert(0, src_path)

def test_database_connection():
    """Test database connection with comprehensive diagnostics"""
    
    print("🔍 Database Connection Diagnostics")
    print("=" * 50)
    
    # Check environment variables
    print("1. 📋 Environment Variables Check:")
    required_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USERNAME', 'DB_PASSWORD']
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask password for security
            display_value = "***" if var == 'DB_PASSWORD' else value
            print(f"   ✅ {var}: {display_value}")
        else:
            print(f"   ❌ {var}: Not set")
    
    # Test basic connection
    print("\n2. 🔌 Basic Connection Test:")
    try:
        import psycopg2
        from psycopg2 import sql
        
        # Connection parameters
        conn_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'clinical_data'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', '')
        }
        
        print(f"   🔗 Connecting to: {conn_params['host']}:{conn_params['port']}/{conn_params['database']}")
        
        # Attempt connection
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        print("   ✅ Connection successful!")
        
        # Test basic query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"   📊 PostgreSQL Version: {version}")
        
        # Test schema access
        cursor.execute("SELECT current_schema();")
        schema = cursor.fetchone()[0]
        print(f"   🗄️ Current Schema: {schema}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except ImportError:
        print("   ❌ psycopg2 not installed")
        print("   💡 Install with: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False

def test_database_executor():
    """Test the DatabaseExecutor class"""
    
    print("\n3. 🔧 DatabaseExecutor Test:")
    try:
        from nlq.database_executor import DatabaseExecutor
        
        executor = DatabaseExecutor()
        print("   ✅ DatabaseExecutor initialized")
        
        # Connect first (required before test_connection)
        connect_success = executor.connect()
        if not connect_success:
            print("   ❌ DatabaseExecutor connect() failed")
            return False
        
        print("   ✅ DatabaseExecutor connected successfully")
        
        # Test connection
        connection_test = executor.test_connection()
        
        if connection_test['success']:
            print("   ✅ DatabaseExecutor connection test passed")
            print(f"   📊 Response time: {connection_test.get('response_time', 'N/A')}ms")
            
            # Test simple query
            print("\n   🔍 Testing simple query...")
            result = executor.execute_query("SELECT 1 as test_value;")
            
            if result['success']:
                print("   ✅ Simple query executed successfully")
                print(f"   📊 Data: {result['data']}")
                return True
            else:
                print(f"   ❌ Simple query failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"   ❌ DatabaseExecutor connection test failed: {connection_test.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"   ❌ DatabaseExecutor test failed: {e}")
        return False

def test_clinical_tables():
    """Test access to clinical tables"""
    
    print("\n4. 🏥 Clinical Tables Test:")
    try:
        from nlq.database_executor import DatabaseExecutor
        
        executor = DatabaseExecutor()
        
        # Connect first
        if not executor.connect():
            print("   ❌ Failed to connect to database")
            return False
        
        # Test key clinical tables
        tables_to_test = [
            'clinical_data.patients',
            'clinical_data.conditions',
            'clinical_data.encounters',
            'clinical_data.medications',
            'clinical_data.procedures'
        ]
        
        for table in tables_to_test:
            try:
                result = executor.execute_query(f"SELECT COUNT(*) as count FROM {table} LIMIT 1;")
                if result['success'] and result['data']:
                    count = result['data'][0]['count'] if isinstance(result['data'], list) else result['data'].iloc[0]['count']
                    print(f"   ✅ {table}: {count:,} records")
                else:
                    print(f"   ❌ {table}: Query failed - {result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"   ❌ {table}: Error - {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Clinical tables test failed: {e}")
        return False

def diagnose_connection_issues():
    """Provide connection troubleshooting suggestions"""
    
    print("\n5. 🔧 Connection Troubleshooting:")
    
    # Check if PostgreSQL is running
    print("   💡 Troubleshooting Steps:")
    print("   1. Ensure PostgreSQL is running on your system")
    print("   2. Check if the database 'clinical_data' exists")
    print("   3. Verify user credentials and permissions")
    print("   4. Check firewall settings (port 5432)")
    print("   5. Verify .env file has correct database settings")
    
    print("\n   🔍 Common Solutions:")
    print("   - Start PostgreSQL service: net start postgresql-x64-14")
    print("   - Create database: createdb clinical_data")
    print("   - Check connection string in .env file")
    print("   - Ensure user has database access permissions")

if __name__ == "__main__":
    print("🔍 Clinical NLQ Database Connection Test")
    print("=" * 60)
    
    # Test 1: Environment variables
    env_ok = True
    required_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USERNAME', 'DB_PASSWORD']
    for var in required_vars:
        if not os.getenv(var):
            env_ok = False
            break
    
    # Test 2: Basic connection
    conn_ok = test_database_connection()
    
    # Test 3: DatabaseExecutor
    executor_ok = test_database_executor() if conn_ok else False
    
    # Test 4: Clinical tables
    tables_ok = test_clinical_tables() if executor_ok else False
    
    # Results summary
    print("\n" + "=" * 60)
    print("📊 Database Connection Test Results:")
    print(f"Environment Variables: {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"Basic Connection: {'✅ PASS' if conn_ok else '❌ FAIL'}")
    print(f"DatabaseExecutor: {'✅ PASS' if executor_ok else '❌ FAIL'}")
    print(f"Clinical Tables: {'✅ PASS' if tables_ok else '❌ FAIL'}")
    
    if all([env_ok, conn_ok, executor_ok, tables_ok]):
        print("\n🎉 All database tests passed! Database is properly connected.")
    else:
        print("\n⚠️ Some database tests failed. See troubleshooting suggestions below.")
        diagnose_connection_issues()