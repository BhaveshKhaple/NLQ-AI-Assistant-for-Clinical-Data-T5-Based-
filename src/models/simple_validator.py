#!/usr/bin/env python3
"""
Simple Training Data Validation Script
Validates generated NLQ-SQL pairs for syntax and schema compliance without database connection.
"""

import json
import sqlparse
import re
from typing import List, Dict, Tuple
from collections import defaultdict

class SimpleValidator:
    def __init__(self):
        """Initialize the validator with expected schema information."""
        # Define expected tables and columns based on schema.sql
        self.expected_tables = {
            'patients': {
                'id', 'birth_date', 'death_date', 'ssn', 'drivers', 'passport', 
                'prefix', 'first_name', 'middle_name', 'last_name', 'suffix', 
                'maiden_name', 'marital_status', 'race', 'ethnicity', 'gender', 
                'birth_place', 'address', 'city', 'state', 'county', 'fips', 
                'zip', 'latitude', 'longitude', 'healthcare_expenses', 
                'healthcare_coverage', 'income', 'created_at', 'updated_at'
            },
            'organizations': {
                'id', 'name', 'address', 'city', 'state', 'zip', 'latitude', 
                'longitude', 'phone', 'revenue', 'utilization', 'created_at'
            },
            'providers': {
                'id', 'organization_id', 'name', 'gender', 'speciality', 'address', 
                'city', 'state', 'zip', 'latitude', 'longitude', 'utilization', 'created_at'
            },
            'encounters': {
                'id', 'start_time', 'stop_time', 'patient_id', 'organization_id', 
                'provider_id', 'payer_id', 'encounter_class', 'code', 'description', 
                'base_encounter_cost', 'total_claim_cost', 'payer_coverage', 
                'reason_code', 'reason_description', 'created_at'
            },
            'conditions': {
                'id', 'start_date', 'stop_date', 'patient_id', 'encounter_id', 
                'system', 'code', 'description', 'created_at'
            },
            'medications': {
                'id', 'start_date', 'stop_date', 'patient_id', 'payer_id', 
                'encounter_id', 'code', 'description', 'base_cost', 'payer_coverage', 
                'dispenses', 'total_cost', 'reason_code', 'reason_description', 'created_at'
            },
            'procedures': {
                'id', 'date', 'patient_id', 'encounter_id', 'system', 'code', 
                'description', 'base_cost', 'reason_code', 'reason_description', 'created_at'
            },
            'observations': {
                'id', 'date', 'patient_id', 'encounter_id', 'category', 'system', 
                'code', 'description', 'value', 'units', 'type', 'created_at'
            },
            'immunizations': {
                'id', 'date', 'patient_id', 'encounter_id', 'code', 'description', 
                'base_cost', 'created_at'
            },
            'allergies': {
                'id', 'start_date', 'stop_date', 'patient_id', 'encounter_id', 
                'system', 'code', 'category', 'reaction1', 'description1', 'severity1', 
                'reaction2', 'description2', 'severity2', 'created_at'
            },
            'care_plans': {
                'id', 'start_date', 'stop_date', 'patient_id', 'encounter_id', 
                'system', 'code', 'description', 'reason_code', 'reason_description', 'created_at'
            },
            'payers': {
                'id', 'name', 'ownership', 'address', 'city', 'state', 'zip', 'phone', 
                'amount_covered', 'amount_uncovered', 'revenue', 'covered_encounters', 
                'uncovered_encounters', 'covered_medications', 'uncovered_medications', 
                'covered_procedures', 'uncovered_procedures', 'covered_immunizations', 
                'uncovered_immunizations', 'unique_customers', 'qols_avg', 'member_months', 'created_at'
            }
        }
    
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
            
            # Check for common syntax issues
            if sql.count('(') != sql.count(')'):
                return False, "Mismatched parentheses"
            
            if sql.count("'") % 2 != 0:
                return False, "Unmatched single quotes"
            
            return True, "Valid syntax"
            
        except Exception as e:
            return False, f"Syntax error: {str(e)}"
    
    def validate_schema_references(self, sql: str) -> Tuple[bool, List[str]]:
        """Validate that SQL references valid tables and columns."""
        issues = []
        
        # Extract table references (clinical_data.table_name)
        table_pattern = r'clinical_data\.(\w+)'
        referenced_tables = set(re.findall(table_pattern, sql, re.IGNORECASE))
        
        # Check if tables exist
        for table in referenced_tables:
            if table not in self.expected_tables:
                issues.append(f"Unknown table 'clinical_data.{table}'")
        
        # Extract column references in SELECT, WHERE, ORDER BY, GROUP BY
        column_patterns = [
            r'SELECT\s+.*?(\w+\.\w+)',  # SELECT table.column
            r'WHERE\s+.*?(\w+\.\w+)',   # WHERE table.column
            r'ORDER BY\s+(\w+\.\w+)',   # ORDER BY table.column
            r'GROUP BY\s+(\w+\.\w+)',   # GROUP BY table.column
            r'HAVING\s+.*?(\w+\.\w+)',  # HAVING table.column
        ]
        
        # This is a simplified validation - a full parser would be more accurate
        for pattern in column_patterns:
            matches = re.findall(pattern, sql, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if '.' in match:
                    table_alias, column = match.split('.', 1)
                    # Note: This doesn't handle aliases properly - would need more sophisticated parsing
        
        return len(issues) == 0, issues
    
    def check_common_sql_patterns(self, sql: str) -> Tuple[bool, List[str]]:
        """Check for common SQL pattern issues."""
        issues = []
        
        # Check for proper schema prefix
        if 'FROM ' in sql.upper() and 'clinical_data.' not in sql:
            # Look for table names without schema prefix
            from_pattern = r'FROM\s+(\w+)'
            matches = re.findall(from_pattern, sql, re.IGNORECASE)
            for match in matches:
                if match.lower() in [t.lower() for t in self.expected_tables.keys()]:
                    issues.append(f"Table '{match}' should be prefixed with 'clinical_data.'")
        
        # Check for proper JOIN syntax
        if 'JOIN' in sql.upper():
            # Basic check for JOIN ... ON pattern
            join_pattern = r'JOIN\s+\w+.*?ON'
            if not re.search(join_pattern, sql, re.IGNORECASE | re.DOTALL):
                issues.append("JOIN clause may be missing ON condition")
        
        # Check for GROUP BY with aggregate functions
        if 'GROUP BY' in sql.upper():
            if not any(func in sql.upper() for func in ['COUNT(', 'SUM(', 'AVG(', 'MAX(', 'MIN(']):
                issues.append("GROUP BY used without aggregate functions")
        
        # Check for proper ILIKE usage (PostgreSQL specific)
        if 'LIKE' in sql.upper() and 'ILIKE' not in sql.upper():
            issues.append("Consider using ILIKE instead of LIKE for case-insensitive matching")
        
        return len(issues) == 0, issues
    
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
        
        # 2. Schema reference validation
        schema_valid, schema_issues = self.validate_schema_references(sql)
        if not schema_valid:
            result['valid'] = False
            result['issues'].extend([f"Schema: {issue}" for issue in schema_issues])
        
        # 3. Common pattern validation
        pattern_valid, pattern_issues = self.check_common_sql_patterns(sql)
        if not pattern_valid:
            # These are warnings, not errors
            result['issues'].extend([f"Warning: {issue}" for issue in pattern_issues])
        
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
            'queries_with_warnings': 0,
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
            
            # Count errors vs warnings
            has_errors = any('Syntax:' in issue or 'Schema:' in issue for issue in validation_result['issues'])
            has_warnings = any('Warning:' in issue for issue in validation_result['issues'])
            
            if has_errors:
                results['invalid_queries'] += 1
                results['issues_by_category'][item['category']].extend(validation_result['issues'])
            else:
                results['valid_queries'] += 1
                if has_warnings:
                    results['queries_with_warnings'] += 1
            
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
        warnings = results['queries_with_warnings']
        
        report = f"""
# Training Data Validation Report

## Summary
- **Total Queries**: {total}
- **Valid Queries**: {valid} ({valid/total*100:.1f}%)
- **Invalid Queries**: {invalid} ({invalid/total*100:.1f}%)
- **Queries with Warnings**: {warnings} ({warnings/total*100:.1f}%)

## Validation Status
{'✅ All queries are syntactically valid!' if invalid == 0 else f'❌ {invalid} queries have critical issues that need fixing'}
{f'⚠️  {warnings} queries have warnings (non-critical issues)' if warnings > 0 else ''}

## Issue Summary
"""
        
        if results['common_issues']:
            for issue_type, count in sorted(results['common_issues'].items(), key=lambda x: x[1], reverse=True):
                report += f"- **{issue_type}**: {count} occurrences\n"
        else:
            report += "- No issues found!\n"
        
        # Show sample invalid queries
        if invalid > 0:
            report += "\n## Sample Invalid Queries (First 5)\n"
            invalid_examples = [r for r in results['validation_results'] if not r['valid']][:5]
            
            for i, example in enumerate(invalid_examples, 1):
                report += f"\n### Example {i}\n"
                report += f"**NLQ**: {example['nlq']}\n"
                report += f"**SQL**: ```sql\n{example['sql']}\n```\n"
                report += f"**Category**: {example['category']}\n"
                report += f"**Issues**: {', '.join(example['issues'])}\n"
        
        # Show sample queries with warnings
        if warnings > 0:
            report += "\n## Sample Queries with Warnings (First 5)\n"
            warning_examples = [r for r in results['validation_results'] 
                              if r['valid'] and any('Warning:' in issue for issue in r['issues'])][:5]
            
            for i, example in enumerate(warning_examples, 1):
                report += f"\n### Warning Example {i}\n"
                report += f"**NLQ**: {example['nlq']}\n"
                report += f"**SQL**: ```sql\n{example['sql']}\n```\n"
                report += f"**Category**: {example['category']}\n"
                report += f"**Warnings**: {', '.join([issue for issue in example['issues'] if 'Warning:' in issue])}\n"
        
        print(report)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n📄 Validation report saved to: {output_path}")
        
        return report

def main():
    """Main validation function."""
    print("🚀 Starting Training Data Validation...")
    
    # Initialize validator
    validator = SimpleValidator()
    
    # Validate the dataset
    dataset_path = "d:/projects/healthca/data/processed/clinical_nlq_training_data.json"
    results = validator.validate_dataset(dataset_path)
    
    # Generate report
    report_path = "d:/projects/healthca/data/processed/validation_report.md"
    validator.generate_validation_report(results, report_path)
    
    print(f"\n✅ Validation complete!")
    print(f"📊 Results: {results['valid_queries']}/{results['total_queries']} queries are valid")
    
    if results['invalid_queries'] > 0:
        print(f"❌ {results['invalid_queries']} queries need fixing")
        print("📄 Check validation_report.md for details")
    
    return results

if __name__ == "__main__":
    main()