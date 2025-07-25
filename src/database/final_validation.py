#!/usr/bin/env python3
"""
Final Comprehensive Validation
Performs a complete end-to-end validation of the clinical database setup
"""

import psycopg2
from sqlalchemy import create_engine, text
import pandas as pd
import logging
from urllib.parse import quote_plus
from datetime import datetime
import json
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FinalValidator:
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
        
        self.validation_results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'UNKNOWN',
            'tests_passed': 0,
            'tests_failed': 0,
            'critical_issues': [],
            'warnings': [],
            'summary': {}
        }
    
    def test_database_connectivity(self) -> bool:
        """Test basic database connectivity"""
        logger.info("Testing database connectivity...")
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                if result.scalar() == 1:
                    logger.info("✅ Database connectivity: PASSED")
                    return True
                else:
                    logger.error("❌ Database connectivity: FAILED")
                    return False
        except Exception as e:
            logger.error(f"❌ Database connectivity: FAILED - {e}")
            self.validation_results['critical_issues'].append(f"Database connectivity failed: {e}")
            return False
    
    def test_schema_existence(self) -> bool:
        """Test that clinical_data schema exists"""
        logger.info("Testing schema existence...")
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT COUNT(*) 
                    FROM information_schema.schemata 
                    WHERE schema_name = 'clinical_data'
                """))
                if result.scalar() == 1:
                    logger.info("✅ Schema existence: PASSED")
                    return True
                else:
                    logger.error("❌ Schema existence: FAILED")
                    self.validation_results['critical_issues'].append("clinical_data schema does not exist")
                    return False
        except Exception as e:
            logger.error(f"❌ Schema existence: FAILED - {e}")
            self.validation_results['critical_issues'].append(f"Schema check failed: {e}")
            return False
    
    def test_table_existence(self) -> bool:
        """Test that all required tables exist"""
        logger.info("Testing table existence...")
        required_tables = ['patients', 'organizations', 'providers', 'payers', 'encounters', 'conditions', 'medications']
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'clinical_data'
                """))
                existing_tables = [row[0] for row in result.fetchall()]
                
                missing_tables = set(required_tables) - set(existing_tables)
                
                if not missing_tables:
                    logger.info(f"✅ Table existence: PASSED ({len(existing_tables)} tables found)")
                    return True
                else:
                    logger.error(f"❌ Table existence: FAILED - Missing tables: {missing_tables}")
                    self.validation_results['critical_issues'].append(f"Missing tables: {missing_tables}")
                    return False
        except Exception as e:
            logger.error(f"❌ Table existence: FAILED - {e}")
            self.validation_results['critical_issues'].append(f"Table check failed: {e}")
            return False
    
    def test_data_presence(self) -> bool:
        """Test that tables contain data"""
        logger.info("Testing data presence...")
        tables_with_min_rows = {
            'patients': 50,
            'organizations': 10,
            'providers': 10,
            'payers': 5,
            'encounters': 100,
            'conditions': 50,
            'medications': 50
        }
        
        all_passed = True
        
        try:
            with self.engine.connect() as conn:
                for table, min_rows in tables_with_min_rows.items():
                    result = conn.execute(text(f"SELECT COUNT(*) FROM clinical_data.{table}"))
                    row_count = result.scalar()
                    
                    if row_count >= min_rows:
                        logger.info(f"✅ {table}: {row_count:,} rows (minimum {min_rows})")
                    else:
                        logger.error(f"❌ {table}: {row_count:,} rows (minimum {min_rows} required)")
                        self.validation_results['critical_issues'].append(f"{table} has insufficient data: {row_count} < {min_rows}")
                        all_passed = False
                
                if all_passed:
                    logger.info("✅ Data presence: PASSED")
                else:
                    logger.error("❌ Data presence: FAILED")
                
                return all_passed
        
        except Exception as e:
            logger.error(f"❌ Data presence: FAILED - {e}")
            self.validation_results['critical_issues'].append(f"Data presence check failed: {e}")
            return False
    
    def test_referential_integrity(self) -> bool:
        """Test referential integrity"""
        logger.info("Testing referential integrity...")
        
        integrity_checks = [
            ("providers.organization_id", "organizations.id"),
            ("encounters.patient_id", "patients.id"),
            ("encounters.provider_id", "providers.id"),
            ("encounters.organization_id", "organizations.id"),
            ("conditions.patient_id", "patients.id"),
            ("medications.patient_id", "patients.id")
        ]
        
        all_passed = True
        
        try:
            with self.engine.connect() as conn:
                for child_ref, parent_ref in integrity_checks:
                    child_table, child_col = child_ref.split('.')
                    parent_table, parent_col = parent_ref.split('.')
                    
                    result = conn.execute(text(f"""
                        SELECT COUNT(*) 
                        FROM clinical_data.{child_table} c
                        LEFT JOIN clinical_data.{parent_table} p ON c.{child_col} = p.{parent_col}
                        WHERE c.{child_col} IS NOT NULL AND p.{parent_col} IS NULL
                    """))
                    
                    orphaned_count = result.scalar()
                    
                    if orphaned_count == 0:
                        logger.info(f"✅ {child_ref} -> {parent_ref}: OK")
                    else:
                        logger.error(f"❌ {child_ref} -> {parent_ref}: {orphaned_count} orphaned records")
                        self.validation_results['critical_issues'].append(f"Referential integrity violation: {child_ref} -> {parent_ref}")
                        all_passed = False
                
                if all_passed:
                    logger.info("✅ Referential integrity: PASSED")
                else:
                    logger.error("❌ Referential integrity: FAILED")
                
                return all_passed
        
        except Exception as e:
            logger.error(f"❌ Referential integrity: FAILED - {e}")
            self.validation_results['critical_issues'].append(f"Referential integrity check failed: {e}")
            return False
    
    def test_sample_queries(self) -> bool:
        """Test sample NLQ queries"""
        logger.info("Testing sample queries...")
        
        sample_queries = [
            {
                'name': 'patient_count',
                'sql': 'SELECT COUNT(*) FROM clinical_data.patients',
                'expected_min': 1
            },
            {
                'name': 'patient_demographics',
                'sql': 'SELECT gender, COUNT(*) FROM clinical_data.patients GROUP BY gender',
                'expected_min': 1
            },
            {
                'name': 'common_conditions',
                'sql': 'SELECT description, COUNT(*) as freq FROM clinical_data.conditions GROUP BY description ORDER BY freq DESC LIMIT 5',
                'expected_min': 1
            },
            {
                'name': 'patient_encounters',
                'sql': 'SELECT p.first_name, p.last_name, COUNT(e.id) FROM clinical_data.patients p LEFT JOIN clinical_data.encounters e ON p.id = e.patient_id GROUP BY p.id, p.first_name, p.last_name LIMIT 5',
                'expected_min': 1
            }
        ]
        
        all_passed = True
        
        try:
            with self.engine.connect() as conn:
                for query in sample_queries:
                    try:
                        start_time = datetime.now()
                        result = conn.execute(text(query['sql']))
                        rows = result.fetchall()
                        end_time = datetime.now()
                        
                        execution_time = (end_time - start_time).total_seconds()
                        row_count = len(rows)
                        
                        if row_count >= query['expected_min'] and execution_time < 1.0:
                            logger.info(f"✅ {query['name']}: {row_count} rows in {execution_time:.4f}s")
                        else:
                            logger.error(f"❌ {query['name']}: {row_count} rows in {execution_time:.4f}s (expected ≥{query['expected_min']} rows, <1s)")
                            self.validation_results['warnings'].append(f"Query performance issue: {query['name']}")
                            all_passed = False
                    
                    except Exception as e:
                        logger.error(f"❌ {query['name']}: Query failed - {e}")
                        self.validation_results['critical_issues'].append(f"Query failed: {query['name']} - {e}")
                        all_passed = False
                
                if all_passed:
                    logger.info("✅ Sample queries: PASSED")
                else:
                    logger.error("❌ Sample queries: FAILED")
                
                return all_passed
        
        except Exception as e:
            logger.error(f"❌ Sample queries: FAILED - {e}")
            self.validation_results['critical_issues'].append(f"Sample queries check failed: {e}")
            return False
    
    def test_indexes_existence(self) -> bool:
        """Test that performance indexes exist"""
        logger.info("Testing index existence...")
        
        expected_indexes = [
            'idx_patients_gender',
            'idx_conditions_patient_id',
            'idx_conditions_description',
            'idx_encounters_patient_id',
            'idx_encounters_organization_id',
            'idx_medications_patient_id'
        ]
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE schemaname = 'clinical_data'
                """))
                existing_indexes = [row[0] for row in result.fetchall()]
                
                missing_indexes = set(expected_indexes) - set(existing_indexes)
                
                if not missing_indexes:
                    logger.info(f"✅ Index existence: PASSED ({len(existing_indexes)} indexes found)")
                    return True
                else:
                    logger.warning(f"⚠️ Index existence: Some indexes missing: {missing_indexes}")
                    self.validation_results['warnings'].append(f"Missing indexes: {missing_indexes}")
                    return True  # Not critical, just a warning
        
        except Exception as e:
            logger.error(f"❌ Index existence: FAILED - {e}")
            self.validation_results['warnings'].append(f"Index check failed: {e}")
            return True  # Not critical
    
    def test_documentation_existence(self) -> bool:
        """Test that required documentation exists"""
        logger.info("Testing documentation existence...")
        
        required_docs = [
            'docs/database_setup_guide.md',
            'docs/database_validation_report.md',
            'docs/nlq_performance_report.md',
            'docs/project_status_summary.md'
        ]
        
        missing_docs = []
        
        for doc_path in required_docs:
            full_path = Path(r'd:\projects\healthca') / doc_path
            if not full_path.exists():
                missing_docs.append(doc_path)
        
        if not missing_docs:
            logger.info(f"✅ Documentation existence: PASSED ({len(required_docs)} documents found)")
            return True
        else:
            logger.warning(f"⚠️ Documentation existence: Missing documents: {missing_docs}")
            self.validation_results['warnings'].append(f"Missing documentation: {missing_docs}")
            return True  # Not critical, just a warning
    
    def generate_final_summary(self) -> dict:
        """Generate final validation summary"""
        logger.info("Generating final summary...")
        
        total_tests = self.validation_results['tests_passed'] + self.validation_results['tests_failed']
        success_rate = (self.validation_results['tests_passed'] / total_tests * 100) if total_tests > 0 else 0
        
        # Determine overall status
        if self.validation_results['critical_issues']:
            overall_status = 'FAILED'
        elif self.validation_results['tests_failed'] > 0:
            overall_status = 'PARTIAL'
        elif self.validation_results['warnings']:
            overall_status = 'PASSED_WITH_WARNINGS'
        else:
            overall_status = 'EXCELLENT'
        
        self.validation_results['overall_status'] = overall_status
        
        summary = {
            'overall_status': overall_status,
            'success_rate': round(success_rate, 1),
            'tests_passed': self.validation_results['tests_passed'],
            'tests_failed': self.validation_results['tests_failed'],
            'critical_issues_count': len(self.validation_results['critical_issues']),
            'warnings_count': len(self.validation_results['warnings']),
            'ready_for_production': overall_status in ['EXCELLENT', 'PASSED_WITH_WARNINGS']
        }
        
        self.validation_results['summary'] = summary
        return summary
    
    def run_final_validation(self) -> bool:
        """Run complete final validation"""
        logger.info("=" * 60)
        logger.info("STARTING FINAL COMPREHENSIVE VALIDATION")
        logger.info("=" * 60)
        
        # Run all validation tests
        tests = [
            ('Database Connectivity', self.test_database_connectivity),
            ('Schema Existence', self.test_schema_existence),
            ('Table Existence', self.test_table_existence),
            ('Data Presence', self.test_data_presence),
            ('Referential Integrity', self.test_referential_integrity),
            ('Sample Queries', self.test_sample_queries),
            ('Index Existence', self.test_indexes_existence),
            ('Documentation Existence', self.test_documentation_existence)
        ]
        
        for test_name, test_func in tests:
            logger.info(f"\n--- {test_name} ---")
            try:
                if test_func():
                    self.validation_results['tests_passed'] += 1
                else:
                    self.validation_results['tests_failed'] += 1
            except Exception as e:
                logger.error(f"Test {test_name} encountered an error: {e}")
                self.validation_results['tests_failed'] += 1
                self.validation_results['critical_issues'].append(f"{test_name} failed with error: {e}")
        
        # Generate summary
        summary = self.generate_final_summary()
        
        # Final report
        logger.info("\n" + "=" * 60)
        logger.info("FINAL VALIDATION RESULTS")
        logger.info("=" * 60)
        logger.info(f"Overall Status: {summary['overall_status']}")
        logger.info(f"Success Rate: {summary['success_rate']}%")
        logger.info(f"Tests Passed: {summary['tests_passed']}")
        logger.info(f"Tests Failed: {summary['tests_failed']}")
        logger.info(f"Critical Issues: {summary['critical_issues_count']}")
        logger.info(f"Warnings: {summary['warnings_count']}")
        logger.info(f"Ready for Production: {'YES' if summary['ready_for_production'] else 'NO'}")
        
        if self.validation_results['critical_issues']:
            logger.info("\nCRITICAL ISSUES:")
            for issue in self.validation_results['critical_issues']:
                logger.error(f"  ❌ {issue}")
        
        if self.validation_results['warnings']:
            logger.info("\nWARNINGS:")
            for warning in self.validation_results['warnings']:
                logger.warning(f"  ⚠️ {warning}")
        
        if summary['overall_status'] == 'EXCELLENT':
            logger.info("\n🎉 VALIDATION COMPLETED SUCCESSFULLY!")
            logger.info("✅ Database is ready for NLQ development")
        elif summary['ready_for_production']:
            logger.info("\n✅ VALIDATION PASSED WITH MINOR WARNINGS")
            logger.info("✅ Database is ready for NLQ development")
        else:
            logger.info("\n❌ VALIDATION FAILED")
            logger.info("❌ Database requires fixes before proceeding")
        
        logger.info("=" * 60)
        
        # Save validation results
        output_path = Path(r'd:\projects\healthca\docs') / 'final_validation_report.json'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.validation_results, f, indent=2, default=str)
        
        logger.info(f"Final validation report saved to: {output_path}")
        
        return summary['ready_for_production']

def main():
    """Main execution function"""
    validator = FinalValidator()
    success = validator.run_final_validation()
    return success

if __name__ == "__main__":
    main()