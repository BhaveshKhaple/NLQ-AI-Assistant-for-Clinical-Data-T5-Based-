#!/usr/bin/env python3
"""
Generate Entity-Relationship Diagram (ERD) for Clinical Database
Creates both visual diagrams and comprehensive documentation
"""

import json
import logging
from pathlib import Path
from datetime import datetime
import psycopg2
from sqlalchemy import create_engine, text, inspect
from urllib.parse import quote_plus

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ERDGenerator:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'medical',
            'user': 'postgres',
            'password': 'Pass@123'
        }
        
        # Create connection
        password_encoded = quote_plus(self.db_config['password'])
        connection_string = (
            f"postgresql://{self.db_config['user']}:{password_encoded}"
            f"@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
        )
        self.engine = create_engine(connection_string)
        
    def extract_database_schema(self):
        """Extract complete schema information from the database"""
        logger.info("Extracting database schema information...")
        
        inspector = inspect(self.engine)
        schema_info = {
            'tables': {},
            'relationships': [],
            'indexes': {},
            'views': []
        }
        
        # Get all tables in clinical_data schema
        tables = inspector.get_table_names(schema='clinical_data')
        logger.info(f"Found {len(tables)} tables in clinical_data schema")
        
        for table_name in tables:
            logger.info(f"Analyzing table: {table_name}")
            
            # Get columns
            columns = inspector.get_columns(table_name, schema='clinical_data')
            
            # Get primary keys
            pk_constraint = inspector.get_pk_constraint(table_name, schema='clinical_data')
            primary_keys = pk_constraint.get('constrained_columns', [])
            
            # Get foreign keys
            foreign_keys = inspector.get_foreign_keys(table_name, schema='clinical_data')
            
            # Get indexes
            indexes = inspector.get_indexes(table_name, schema='clinical_data')
            
            # Get unique constraints
            unique_constraints = inspector.get_unique_constraints(table_name, schema='clinical_data')
            
            # Get check constraints
            check_constraints = inspector.get_check_constraints(table_name, schema='clinical_data')
            
            # Process columns
            processed_columns = []
            for col in columns:
                column_info = {
                    'name': col['name'],
                    'type': str(col['type']),
                    'nullable': col['nullable'],
                    'default': col.get('default'),
                    'primary_key': col['name'] in primary_keys,
                    'foreign_key': False,
                    'references': None
                }
                
                # Check if it's a foreign key
                for fk in foreign_keys:
                    if col['name'] in fk['constrained_columns']:
                        column_info['foreign_key'] = True
                        fk_index = fk['constrained_columns'].index(col['name'])
                        column_info['references'] = {
                            'table': fk['referred_table'],
                            'column': fk['referred_columns'][fk_index],
                            'schema': fk.get('referred_schema', 'clinical_data')
                        }
                        break
                
                processed_columns.append(column_info)
            
            schema_info['tables'][table_name] = {
                'columns': processed_columns,
                'primary_keys': primary_keys,
                'foreign_keys': foreign_keys,
                'indexes': indexes,
                'unique_constraints': unique_constraints,
                'check_constraints': check_constraints
            }
            
            # Add relationships
            for fk in foreign_keys:
                for i, col in enumerate(fk['constrained_columns']):
                    schema_info['relationships'].append({
                        'from_table': table_name,
                        'from_column': col,
                        'to_table': fk['referred_table'],
                        'to_column': fk['referred_columns'][i],
                        'constraint_name': fk['name']
                    })
        
        # Get views
        try:
            views = inspector.get_view_names(schema='clinical_data')
            schema_info['views'] = views
            logger.info(f"Found {len(views)} views")
        except Exception as e:
            logger.warning(f"Could not retrieve views: {e}")
        
        return schema_info
    
    def get_table_statistics(self):
        """Get row counts and other statistics for each table"""
        logger.info("Gathering table statistics...")
        
        stats = {}
        
        try:
            with self.engine.connect() as conn:
                # Get table sizes
                result = conn.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        attname,
                        n_distinct,
                        null_frac
                    FROM pg_stats 
                    WHERE schemaname = 'clinical_data'
                    ORDER BY tablename, attname
                """))
                
                column_stats = {}
                for row in result:
                    table_key = f"{row.schemaname}.{row.tablename}"
                    if table_key not in column_stats:
                        column_stats[table_key] = {}
                    
                    column_stats[table_key][row.attname] = {
                        'n_distinct': row.n_distinct,
                        'null_frac': row.null_frac
                    }
                
                # Get row counts
                tables = ['patients', 'organizations', 'providers', 'payers', 'encounters', 
                         'conditions', 'medications', 'procedures', 'observations', 
                         'immunizations', 'allergies', 'care_plans']
                
                for table in tables:
                    try:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM clinical_data.{table}"))
                        row_count = result.scalar()
                        
                        stats[table] = {
                            'row_count': row_count,
                            'columns': column_stats.get(f'clinical_data.{table}', {})
                        }
                    except Exception as e:
                        logger.warning(f"Could not get stats for {table}: {e}")
                        stats[table] = {'row_count': 0, 'columns': {}}
        
        except Exception as e:
            logger.error(f"Error gathering statistics: {e}")
        
        return stats
    
    def generate_mermaid_erd(self, schema_info, stats):
        """Generate Mermaid ERD diagram code"""
        logger.info("Generating Mermaid ERD diagram...")
        
        mermaid_lines = [
            "```mermaid",
            "erDiagram",
            ""
        ]
        
        # Define entities
        for table_name, table_info in schema_info['tables'].items():
            if stats.get(table_name, {}).get('row_count', 0) > 0:  # Only include tables with data
                mermaid_lines.append(f"    {table_name.upper()} {{")
                
                for col in table_info['columns']:
                    col_type = col['type'].split('(')[0]  # Remove length specifications
                    
                    # Add symbols for key types
                    symbols = []
                    if col['primary_key']:
                        symbols.append('PK')
                    if col['foreign_key']:
                        symbols.append('FK')
                    if not col['nullable']:
                        symbols.append('NOT NULL')
                    
                    symbol_str = f" {','.join(symbols)}" if symbols else ""
                    mermaid_lines.append(f"        {col_type} {col['name']}{symbol_str}")
                
                mermaid_lines.append("    }")
                mermaid_lines.append("")
        
        # Define relationships
        for rel in schema_info['relationships']:
            from_table = rel['from_table'].upper()
            to_table = rel['to_table'].upper()
            
            # Only include relationships where both tables have data
            if (stats.get(rel['from_table'], {}).get('row_count', 0) > 0 and 
                stats.get(rel['to_table'], {}).get('row_count', 0) > 0):
                
                mermaid_lines.append(f"    {from_table} ||--o{{ {to_table} : {rel['from_column']}")
        
        mermaid_lines.append("```")
        
        return '\n'.join(mermaid_lines)
    
    def generate_comprehensive_documentation(self, schema_info, stats):
        """Generate comprehensive ERD documentation"""
        logger.info("Generating comprehensive ERD documentation...")
        
        doc_lines = [
            "# Clinical Database Entity-Relationship Diagram (ERD)",
            f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "## Database Overview",
            f"- **Database**: {self.db_config['database']}",
            f"- **Schema**: clinical_data",
            f"- **Total Tables**: {len(schema_info['tables'])}",
            f"- **Total Views**: {len(schema_info['views'])}",
            f"- **Total Relationships**: {len(schema_info['relationships'])}",
            "",
            "## Table Summary",
            "",
            "| Table | Rows | Columns | Primary Key | Foreign Keys |",
            "|-------|------|---------|-------------|--------------|"
        ]
        
        # Table summary
        for table_name, table_info in schema_info['tables'].items():
            row_count = stats.get(table_name, {}).get('row_count', 0)
            column_count = len(table_info['columns'])
            pk_cols = ', '.join(table_info['primary_keys'])
            fk_count = len(table_info['foreign_keys'])
            
            doc_lines.append(
                f"| {table_name} | {row_count:,} | {column_count} | {pk_cols} | {fk_count} |"
            )
        
        doc_lines.extend(["", "## Entity-Relationship Diagram", ""])
        
        # Add Mermaid diagram
        mermaid_erd = self.generate_mermaid_erd(schema_info, stats)
        doc_lines.append(mermaid_erd)
        
        doc_lines.extend(["", "## Detailed Table Specifications", ""])
        
        # Detailed table documentation
        for table_name, table_info in schema_info['tables'].items():
            row_count = stats.get(table_name, {}).get('row_count', 0)
            
            doc_lines.extend([
                f"### {table_name.title()}",
                f"**Rows**: {row_count:,}",
                f"**Primary Key**: {', '.join(table_info['primary_keys']) if table_info['primary_keys'] else 'None'}",
                "",
                "#### Columns",
                "| Column | Type | Nullable | Default | Constraints |",
                "|--------|------|----------|---------|-------------|"
            ])
            
            for col in table_info['columns']:
                constraints = []
                if col['primary_key']:
                    constraints.append('PRIMARY KEY')
                if col['foreign_key']:
                    ref = col['references']
                    constraints.append(f"FK → {ref['table']}.{ref['column']}")
                if not col['nullable']:
                    constraints.append('NOT NULL')
                
                constraint_str = ', '.join(constraints) if constraints else ''
                default_str = str(col['default']) if col['default'] else ''
                
                doc_lines.append(
                    f"| {col['name']} | {col['type']} | {col['nullable']} | "
                    f"{default_str} | {constraint_str} |"
                )
            
            # Foreign key relationships
            if table_info['foreign_keys']:
                doc_lines.extend(["", "#### Foreign Key Relationships"])
                for fk in table_info['foreign_keys']:
                    for i, col in enumerate(fk['constrained_columns']):
                        doc_lines.append(
                            f"- `{col}` → `{fk['referred_table']}.{fk['referred_columns'][i]}`"
                        )
            
            # Indexes
            if table_info['indexes']:
                doc_lines.extend(["", "#### Indexes"])
                for idx in table_info['indexes']:
                    unique_str = " (UNIQUE)" if idx['unique'] else ""
                    doc_lines.append(f"- `{idx['name']}` on ({', '.join(idx['column_names'])}){unique_str}")
            
            doc_lines.extend(["", ""])
        
        # Relationship matrix
        doc_lines.extend([
            "## Relationship Matrix",
            "",
            "| From Table | From Column | To Table | To Column | Constraint |",
            "|------------|-------------|----------|-----------|------------|"
        ])
        
        for rel in schema_info['relationships']:
            doc_lines.append(
                f"| {rel['from_table']} | {rel['from_column']} | "
                f"{rel['to_table']} | {rel['to_column']} | {rel['constraint_name']} |"
            )
        
        # Views section
        if schema_info['views']:
            doc_lines.extend([
                "",
                "## Database Views",
                ""
            ])
            
            for view in schema_info['views']:
                doc_lines.append(f"- `{view}`")
        
        # Data quality insights
        doc_lines.extend([
            "",
            "## Data Quality Insights",
            ""
        ])
        
        total_rows = sum(stats.get(table, {}).get('row_count', 0) for table in stats)
        populated_tables = sum(1 for table in stats if stats[table].get('row_count', 0) > 0)
        
        doc_lines.extend([
            f"- **Total Records**: {total_rows:,}",
            f"- **Populated Tables**: {populated_tables}/{len(stats)}",
            f"- **Database Size**: Estimated based on row counts",
            ""
        ])
        
        return '\n'.join(doc_lines)
    
    def generate_erd_files(self, output_dir=None):
        """Generate all ERD files"""
        if output_dir is None:
            output_dir = Path(r'd:\projects\healthca\docs')
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract schema and statistics
        schema_info = self.extract_database_schema()
        stats = self.get_table_statistics()
        
        # Generate comprehensive documentation
        erd_doc = self.generate_comprehensive_documentation(schema_info, stats)
        
        # Save documentation
        doc_path = output_dir / 'database_erd.md'
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(erd_doc)
        
        # Save schema info as JSON
        schema_path = output_dir / 'database_schema.json'
        with open(schema_path, 'w', encoding='utf-8') as f:
            json.dump({
                'schema_info': schema_info,
                'statistics': stats,
                'generated_at': datetime.now().isoformat()
            }, f, indent=2, default=str)
        
        logger.info("=" * 60)
        logger.info("ERD GENERATION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"ERD Documentation: {doc_path}")
        logger.info(f"Schema JSON: {schema_path}")
        logger.info(f"Tables analyzed: {len(schema_info['tables'])}")
        logger.info(f"Relationships mapped: {len(schema_info['relationships'])}")
        logger.info("=" * 60)
        
        return doc_path, schema_path

def main():
    """Main execution function"""
    generator = ERDGenerator()
    generator.generate_erd_files()

if __name__ == "__main__":
    main()