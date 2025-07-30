#!/usr/bin/env python3
"""
Demo script showcasing Database Explorer functionality
"""

import os
import sys
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / "src")
sys.path.insert(0, src_path)

from database.database_viewer import DatabaseViewer

def demo_database_explorer():
    """Demonstrate Database Explorer capabilities."""
    print("🎯 Clinical NLQ Database Explorer Demo")
    print("=" * 50)
    
    # Initialize database viewer
    print("\n🔌 Connecting to database...")
    with DatabaseViewer() as db_viewer:
        if not db_viewer.connection:
            print("❌ Failed to connect to database")
            return
        
        print("✅ Connected successfully!")
        
        # 1. Database Overview
        print("\n📊 DATABASE OVERVIEW")
        print("-" * 30)
        overview = db_viewer.get_database_overview()
        print(f"Total Schemas: {len(overview['schemas'])}")
        print(f"Total Tables: {overview['total_tables']}")
        print(f"Total Columns: {overview['total_columns']}")
        print(f"Total Relationships: {len(overview['relationships'])}")
        
        # 2. Schema Information
        print("\n📁 AVAILABLE SCHEMAS")
        print("-" * 30)
        for schema in overview['schemas']:
            print(f"  {schema['schema_name']}: {schema['table_count']} tables")
        
        # 3. Table Information
        print("\n🗂️ CLINICAL DATA TABLES")
        print("-" * 30)
        tables = overview['clinical_data_tables']
        for table in tables[:10]:  # Show first 10 tables
            print(f"  📋 {table['table_name']}")
            print(f"      Columns: {table['column_count']}")
            print(f"      Estimated Rows: {table['estimated_row_count']:,}")
            print(f"      Size: {table['table_size']}")
            print()
        
        if len(tables) > 10:
            print(f"  ... and {len(tables) - 10} more tables")
        
        # 4. Detailed Table Example
        if tables:
            example_table = 'patients'  # Use patients table as example
            print(f"\n🔍 DETAILED VIEW: {example_table.upper()}")
            print("-" * 30)
            
            columns = db_viewer.get_table_columns(example_table)
            print(f"Columns ({len(columns)}):")
            for col in columns[:8]:  # Show first 8 columns
                constraint = f" [{col['constraint_type']}]" if col['constraint_type'] else ""
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                print(f"  • {col['column_name']}: {col['data_type']} {nullable}{constraint}")
            
            if len(columns) > 8:
                print(f"  ... and {len(columns) - 8} more columns")
            
            # Sample data
            print(f"\nSample Data:")
            sample_data = db_viewer.get_table_sample_data(example_table, limit=3)
            if not sample_data.empty:
                print(f"  Showing 3 of {len(sample_data)} sample rows:")
                for idx, row in sample_data.iterrows():
                    print(f"  Row {idx + 1}: ID={row.get('id', 'N/A')}, "
                          f"Gender={row.get('gender', 'N/A')}, "
                          f"Birth Date={row.get('birth_date', 'N/A')}")
        
        # 5. Relationships
        print(f"\n🔗 TABLE RELATIONSHIPS")
        print("-" * 30)
        relationships = overview['relationships']
        for rel in relationships[:8]:  # Show first 8 relationships
            print(f"  {rel['source_table']}.{rel['source_column']} → {rel['target_table']}.{rel['target_column']}")
        
        if len(relationships) > 8:
            print(f"  ... and {len(relationships) - 8} more relationships")
        
        # 6. Example Queries
        print(f"\n💡 EXAMPLE QUERIES YOU CAN TRY")
        print("-" * 30)
        examples = [
            "How many patients do we have?",
            "Show me all female patients over 65",
            "What are the most common medical conditions?",
            "List all medications prescribed in the last year",
            "Show patient demographics by race and gender",
            "What procedures were performed most frequently?",
            "Find patients with diabetes",
            "Show encounter statistics by type"
        ]
        
        for i, example in enumerate(examples, 1):
            print(f"  {i}. {example}")
        
        print(f"\n🎉 READY TO USE!")
        print("-" * 30)
        print("Your database explorer is ready! You can now:")
        print("1. 🌐 Open the web interface: streamlit run src/ui/streamlit_app.py")
        print("2. 🗄️ Click on the 'Database Explorer' tab")
        print("3. 🔍 Explore your data structure")
        print("4. 💬 Use the 'Query Interface' tab for natural language queries")
        
        print(f"\n📚 For detailed documentation, see: DATABASE_EXPLORER_README.md")

if __name__ == "__main__":
    demo_database_explorer()