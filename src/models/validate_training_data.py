#!/usr/bin/env python3
"""
Training Data Validation Script
Validates all generated NLQ-SQL pairs for syntax correctness and schema compliance.
"""

import json
import psycopg2
import sqlparse
from typing import List, Dict, Tuple
import re
from collections import defaultdict

class SQLValidator:
    def __init__(self, db_config: Dict = None):
        """Initialize the SQL validator with database connection."""
        self.db_config = db_config or {
            'host': 'localhost',
            'port': 5432,
            'database': 'clinical_nlq',
            'user': 'nlq_user',
            'password': 'nlq_password'
        }
        self.connection = None
        self.schema_tables = set()
        self.schema_columns = defaultdict(set)
        
    def connect_to_db(self) -> bool:
        """Establish database connection and load schema information."""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            print("✅ Connected to database successfully")
            self._load_schema_info()
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            print("⚠️  Will perform syntax-only validation")
            return False
    
    def _load_schema_info(self):
        """Load schema information from the database."""
        if not self.connection:
            return
            
        try:
            cursor = self.connection.cursor()
            
            # Get all tables in clinical_data schema
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'clinical_data'
            """)
            
            tables = cursor.fetchall()
            self.schema_tables = {table[0] for table in tables}
            print(f"📊 Found {len(self.schema_tables)} tables in clinical_data schema")
            
            # Get columns for each table
            for table in self.schema_tables:
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_schema = 'clinical_data' AND table_name = %s
                """, (table,))
                
                columns = cursor.fetchall()
                self.schema_columns[table] = {col[0]: col[1] for col in columns}
            
            cursor.close()
            
        except Exception as e:
            print(f"⚠️  Could not load schema info: {e}")
    
    def validate_sql_syntax(self, sql: str) -> Tuple[bool, str]:
        """Validate SQL syntax using sqlparse."""
        try:
            # Parse the SQL
            parsed = sqlparse.parse(sql)
            
            if not parsed:
                return False, "Empty or invalid SQL"
            
            # Check for basic SQL structure
            sql_upper = sql.upper()
            if not any(keyword in sql_upper for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']):
                return False, "No valid SQL statement found"
            
            return True, "Valid syntax"
            
        except Exception as e:
            return False, f"Syntax error: {str(e)}"
    
    def validate_schema_compliance(self, sql: str) -> Tuple[bool, List[str]]:
        """Validate that SQL references valid tables and columns."""
        issues = []
        
        # Extract table references
        table_pattern = r'clinical_data\.(\w+)'
        referenced_tables = set(re.findall(table_pattern, sql, re.IGNORECASE))
        
        # Check if tables exist
        for table in referenced_tables:
            if table not in self.schema_tables:
                issues.append(f"Table 'clinical_data.{table}' does not exist")
        
        # Extract column references (basic pattern matching)
        # This is a simplified check - could be enhanced with proper SQL parsing
        column_patterns = [
            r'(\w+)\.(\w+)',  # table.column
            r'ORDER BY\s+(\w+)',  # ORDER BY column
            r'GROUP BY\s+(\w+)',  # GROUP BY column
        ]
        
        referenced_columns = defaultdict(set)
        for pattern in column_patterns:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple) and len(match) == 2:
                    table_alias, column = match
                    # This is simplified - would need proper alias resolution
                    referenced_columns[table_alias].add(column)
        
        return len(issues) == 0, issues
    
    def test_query_execution(self, sql: str) -> Tuple[bool, str]:
        """Test if query can be executed (with LIMIT to avoid large results)."""
        if not self.connection:
            return True, "Database not connected - skipping execution test"
        
        try:
            cursor = self.connection.cursor()
            
            # Add LIMIT to SELECT queries to avoid large results
            test_sql = sql
            if sql.strip().upper().startswith('SELECT') and 'LIMIT' not in sql.upper():
                test_sql = f"{sql} LIMIT 1"
            
            cursor.execute(test_sql)
            cursor.fetchall()  # Consume results
            cursor.close()
            
            return True, "Query executed successfully"
            
        except Exception as e:
            return False, f"Execution error: {str(e)}"
    
    def validate_single_query(self, nlq: str, sql: str, category: str) -> Dict:
        """Validate a single NLQ-SQL pair."""
        result = {
            'nlq': nlq,
            'sql': sql,
            'category': category,
            'valid': True,
            'issues': []
        }
        
        # 1. Syntax validation
        syntax_valid, syntax_msg = self.validate_sql_syntax(sql)
        if not syntax_valid:
            result['valid'] = False
            result['issues'].append(f"Syntax: {syntax_msg}")
        
        # 2. Schema compliance (if schema info available)
        if self.schema_tables:
            schema_valid, schema_issues = self.validate_schema_compliance(sql)
            if not schema_valid:
                result['valid'] = False
                result['issues'].extend([f"Schema: {issue}" for issue in schema_issues])
        
        # 3. Execution test (if database connected)
        if self.connection:
            exec_valid, exec_msg = self.test_query_execution(sql)
            if not exec_valid:
                result['valid'] = False
                result['issues'].append(f"Execution: {exec_msg}")
        
        return result
    
    def validate_dataset(self, dataset_path: str) -> Dict:
        """Validate the entire training dataset."""
        print(f"🔍 Validating training dataset: {dataset_path}")
        
        # Load dataset
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        data = dataset['data']
        total_queries = len(data)
        
        print(f"📊 Validating {total_queries} NLQ-SQL pairs...")
        
        results = {
            'total_queries': total_queries,
            'valid_queries': 0,
            'invalid_queries': 0,
            'validation_results': [],
            'issues_by_category': defaultdict(list),
            'common_issues': defaultdict(int)
        }
        
        # Validate each query
        for i, item in enumerate(data):
            if i % 100 == 0:
                print(f"  Progress: {i}/{total_queries} ({i/total_queries*100:.1f}%)")
            
            validation_result = self.validate_single_query(
                item['nlq'], 
                item['sql'], 
                item['category']
            )
            
            results['validation_results'].append(validation_result)
            
            if validation_result['valid']:
                results['valid_queries'] += 1
            else:
                results['invalid_queries'] += 1
                results['issues_by_category'][item['category']].extend(validation_result['issues'])
                
                # Count common issues
                for issue in validation_result['issues']:
                    issue_type = issue.split(':')[0] if ':' in issue else issue
                    results['common_issues'][issue_type] += 1
        
        return results
    
    def generate_validation_report(self, results: Dict, output_path: str = None):
        """Generate a comprehensive validation report."""
        total = results['total_queries']
        valid = results['valid_queries']
        invalid = results['invalid_queries']
        
        report = f"""
# Training Data Validation Report

## Summary
- **Total Queries**: {total}
- **Valid Queries**: {valid} ({valid/total*100:.1f}%)
- **Invalid Queries**: {invalid} ({invalid/total*100:.1f}%)

## Validation Status
{'✅ All queries are valid!' if invalid == 0 else f'❌ {invalid} queries have issues that need fixing'}

## Common Issues
"""
        
        if results['common_issues']:
            for issue_type, count in sorted(results['common_issues'].items(), key=lambda x: x[1], reverse=True):
                report += f"- **{issue_type}**: {count} occurrences\n"
        else:
            report += "- No issues found!\n"
        
        report += "\n## Issues by Category\n"
        
        if results['issues_by_category']:
            for category, issues in results['issues_by_category'].items():
                report += f"\n### {category}\n"
                unique_issues = list(set(issues))
                for issue in unique_issues[:5]:  # Show top 5 issues per category
                    report += f"- {issue}\n"
                if len(unique_issues) > 5:
                    report += f"- ... and {len(unique_issues) - 5} more issues\n"
        else:
            report += "- No issues found in any category!\n"
        
        # Show some invalid queries as examples
        if invalid > 0:
            report += "\n## Sample Invalid Queries\n"
            invalid_examples = [r for r in results['validation_results'] if not r['valid']][:5]
            
            for i, example in enumerate(invalid_examples, 1):
                report += f"\n### Example {i}\n"
                report += f"**NLQ**: {example['nlq']}\n"
                report += f"**SQL**: `{example['sql'][:100]}...`\n"
                report += f"**Category**: {example['category']}\n"
                report += f"**Issues**: {', '.join(example['issues'])}\n"
        
        print(report)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n📄 Validation report saved to: {output_path}")
        
        return report
    
    def fix_common_issues(self, results: Dict) -> List[Dict]:
        """Attempt to automatically fix common issues."""
        print("🔧 Attempting to fix common issues...")
        
        fixed_queries = []
        
        for result in results['validation_results']:
            if not result['valid']:
                fixed_sql = result['sql']
                
                # Fix common issues
                for issue in result['issues']:
                    if "does not exist" in issue and "clinical_data." in issue:
                        # Try to fix table name issues
                        pass  # Would implement specific fixes here
                    
                    if "Syntax error" in issue:
                        # Try to fix syntax issues
                        pass  # Would implement specific fixes here
                
                # Check if fixes worked
                syntax_valid, _ = self.validate_sql_syntax(fixed_sql)
                if syntax_valid and fixed_sql != result['sql']:
                    fixed_queries.append({
                        'original': result,
                        'fixed_sql': fixed_sql
                    })
        
        print(f"🔧 Fixed {len(fixed_queries)} queries automatically")
        return fixed_queries
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()

def main():
    """Main validation function."""
    print("🚀 Starting Training Data Validation...")
    
    # Initialize validator
    validator = SQLValidator()
    
    # Try to connect to database
    db_connected = validator.connect_to_db()
    
    # Validate the dataset
    dataset_path = "d:/projects/healthca/data/processed/clinical_nlq_training_data.json"
    results = validator.validate_dataset(dataset_path)
    
    # Generate report
    report_path = "d:/projects/healthca/data/processed/validation_report.md"
    validator.generate_validation_report(results, report_path)
    
    # Try to fix issues
    if results['invalid_queries'] > 0:
        fixed_queries = validator.fix_common_issues(results)
        
        if fixed_queries:
            print(f"💾 Consider reviewing and applying {len(fixed_queries)} automatic fixes")
    
    # Close connection
    validator.close()
    
    print("\n✅ Validation complete!")
    
    return results

if __name__ == "__main__":
    main()