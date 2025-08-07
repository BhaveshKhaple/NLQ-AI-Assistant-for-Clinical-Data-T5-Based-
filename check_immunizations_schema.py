#!/usr/bin/env python3
"""
Check the actual schema of the immunizations table
"""

import sys
import os
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / 'src')
sys.path.insert(0, src_path)

def check_immunizations_schema():
    """Check the actual schema of the immunizations table"""
    
    print("🔍 Checking Immunizations Table Schema")
    print("=" * 50)
    
    try:
        from nlq.database_executor import DatabaseExecutor
        
        db_executor = DatabaseExecutor()
        if not db_executor.connect():
            print("❌ Failed to connect to database")
            return False
        
        print("✅ Database connected successfully")
        
        # Get table schema
        print("\n1. 📋 Getting table columns...")
        schema_query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_schema = 'clinical_data' 
        AND table_name = 'immunizations'
        ORDER BY ordinal_position;
        """
        
        result = db_executor.execute_query(schema_query)
        
        if result['success'] and result['data']:
            print(f"   ✅ Found {len(result['data'])} columns:")
            print("\n   📊 Column Details:")
            for col in result['data']:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"   - {col['column_name']}: {col['data_type']} {nullable}{default}")
        else:
            print(f"   ❌ Failed to get schema: {result.get('error', 'Unknown error')}")
            return False
        
        # Get sample data
        print("\n2. 📊 Getting sample data...")
        sample_query = "SELECT * FROM clinical_data.immunizations LIMIT 3;"
        
        sample_result = db_executor.execute_query(sample_query)
        
        if sample_result['success'] and sample_result['data']:
            print(f"   ✅ Sample data ({len(sample_result['data'])} rows):")
            for i, row in enumerate(sample_result['data'], 1):
                print(f"\n   Row {i}:")
                for key, value in row.items():
                    # Truncate long values
                    display_value = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                    print(f"     {key}: {display_value}")
        else:
            print(f"   ❌ Failed to get sample data: {sample_result.get('error', 'Unknown error')}")
        
        # Check for vaccine-related columns
        print("\n3. 🔍 Looking for vaccine-related columns...")
        vaccine_columns = []
        for col in result['data']:
            col_name = col['column_name'].lower()
            if any(keyword in col_name for keyword in ['vaccine', 'immunization', 'code', 'description', 'display']):
                vaccine_columns.append(col['column_name'])
        
        if vaccine_columns:
            print("   ✅ Found potential vaccine-related columns:")
            for col in vaccine_columns:
                print(f"   - {col}")
        else:
            print("   ⚠️ No obvious vaccine-related columns found")
        
        # Get record count
        print("\n4. 📈 Getting record count...")
        count_query = "SELECT COUNT(*) as total_records FROM clinical_data.immunizations;"
        count_result = db_executor.execute_query(count_query)
        
        if count_result['success'] and count_result['data']:
            total_records = count_result['data'][0]['total_records']
            print(f"   📊 Total immunization records: {total_records:,}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking schema: {e}")
        import traceback
        traceback.print_exc()
        return False

def suggest_correct_query():
    """Suggest the correct query based on actual schema"""
    
    print("\n💡 Query Suggestions")
    print("=" * 30)
    
    print("Based on the schema analysis, here are suggested queries:")
    print("\n🔍 For vaccine names/types:")
    print("   SELECT DISTINCT code FROM clinical_data.immunizations;")
    print("   SELECT DISTINCT description FROM clinical_data.immunizations;")
    print("   SELECT DISTINCT display FROM clinical_data.immunizations;")
    
    print("\n📊 For vaccine statistics:")
    print("   SELECT code, COUNT(*) as count FROM clinical_data.immunizations GROUP BY code;")
    print("   SELECT description, COUNT(*) as count FROM clinical_data.immunizations GROUP BY description;")
    
    print("\n👥 For patient immunizations:")
    print("   SELECT patient, code, date FROM clinical_data.immunizations LIMIT 10;")

if __name__ == "__main__":
    print("🔧 Immunizations Table Schema Analysis")
    print("=" * 60)
    
    success = check_immunizations_schema()
    
    if success:
        suggest_correct_query()
        print("\n🎯 Next Steps:")
        print("1. Update the schema descriptions in the RAG system")
        print("2. Fix the column mappings in the AI model")
        print("3. Test with corrected queries")
    else:
        print("\n❌ Schema analysis failed. Check database connection.")