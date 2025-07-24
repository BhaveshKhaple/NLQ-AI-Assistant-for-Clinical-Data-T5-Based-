#!/usr/bin/env python3
"""
Run the Synthea data import with proper error handling
"""

import os
import sys
import getpass
from import_synthea_data import SyntheaDataImporter

def get_db_config():
    """Get database configuration with password prompt"""
    
    print("=== PostgreSQL Database Configuration ===")
    
    db_config = {
        'host': input("Host (default: localhost): ").strip() or 'localhost',
        'port': int(input("Port (default: 5432): ").strip() or '5432'),
        'database': input("Database (default: medical): ").strip() or 'medical',
        'user': input("Username (default: postgres): ").strip() or 'postgres',
    }
    
    # Get password securely
    db_config['password'] = getpass.getpass("Password: ")
    
    return db_config

def main():
    """Main function with interactive setup"""
    
    print("🏥 Clinical NLQ AI Assistant - Database Setup")
    print("=" * 50)
    
    # Get database configuration
    db_config = get_db_config()
    
    # CSV directory path
    csv_directory = r'd:\projects\healthca\output\csv'
    
    if not os.path.exists(csv_directory):
        print(f"❌ CSV directory not found: {csv_directory}")
        print("Please ensure Synthea data has been generated first.")
        return False
    
    # Create importer instance
    importer = SyntheaDataImporter(db_config, csv_directory)
    
    try:
        print("\n🔌 Testing database connection...")
        if not importer.connect_to_database():
            print("❌ Failed to connect to database.")
            return False
        
        print("✅ Database connection successful!")
        
        print("\n🏗️  Creating database schema...")
        if not importer.create_schema():
            print("❌ Failed to create database schema.")
            return False
        
        print("✅ Database schema created successfully!")
        
        print("\n📊 Importing Synthea data...")
        if not importer.import_all_data():
            print("⚠️  Some data imports failed, but continuing...")
        
        print("\n🔍 Creating additional indexes...")
        importer.create_indexes_and_constraints()
        
        print("\n📈 Generating summary statistics...")
        importer.generate_summary_statistics()
        
        print("\n🎉 Database setup completed successfully!")
        print("\nYour clinical database is now ready for the NLQ AI Assistant!")
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Import interrupted by user")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error during setup: {e}")
        return False
        
    finally:
        importer.close_connections()

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n" + "=" * 50)
        print("🚀 Next Steps:")
        print("1. The database is now populated with synthetic clinical data")
        print("2. You can proceed to Step 4: NLQ Processing Engine")
        print("3. The AI assistant will be able to query this clinical data")
        print("=" * 50)
    
    sys.exit(0 if success else 1)