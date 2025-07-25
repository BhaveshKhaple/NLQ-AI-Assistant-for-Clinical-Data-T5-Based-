#!/usr/bin/env python3
"""
Natural Language Query (NLQ) Tester
Tests database performance with sample queries that would be generated from natural language
"""

import psycopg2
from sqlalchemy import create_engine, text
import pandas as pd
import logging
from urllib.parse import quote_plus
from datetime import datetime, timedelta
import time
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NLQQueryTester:
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
        
        # Test results
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'query_tests': {},
            'performance_summary': {},
            'sample_data': {}
        }
        
        # Sample NLQ queries with their SQL equivalents
        self.sample_queries = [
            {
                'nlq': "How many patients do we have?",
                'sql': "SELECT COUNT(*) as patient_count FROM clinical_data.patients",
                'category': 'basic_count',
                'expected_performance': 0.1
            },
            {
                'nlq': "Show me all female patients",
                'sql': "SELECT first_name, last_name, birth_date FROM clinical_data.patients WHERE gender = 'F'",
                'category': 'basic_filter',
                'expected_performance': 0.2
            },
            {
                'nlq': "What are the most common conditions?",
                'sql': """
                    SELECT description, COUNT(*) as frequency 
                    FROM clinical_data.conditions 
                    GROUP BY description 
                    ORDER BY frequency DESC 
                    LIMIT 10
                """,
                'category': 'aggregation',
                'expected_performance': 0.5
            },
            {
                'nlq': "Show patients with diabetes",
                'sql': """
                    SELECT DISTINCT p.first_name, p.last_name, p.birth_date
                    FROM clinical_data.patients p
                    JOIN clinical_data.conditions c ON p.id = c.patient_id
                    WHERE c.description ILIKE '%diabetes%'
                """,
                'category': 'join_filter',
                'expected_performance': 0.5
            },
            {
                'nlq': "How many encounters did each patient have?",
                'sql': """
                    SELECT p.first_name, p.last_name, COUNT(e.id) as encounter_count
                    FROM clinical_data.patients p
                    LEFT JOIN clinical_data.encounters e ON p.id = e.patient_id
                    GROUP BY p.id, p.first_name, p.last_name
                    ORDER BY encounter_count DESC
                """,
                'category': 'join_aggregation',
                'expected_performance': 1.0
            },
            {
                'nlq': "What medications are prescribed for hypertension?",
                'sql': """
                    SELECT DISTINCT m.description as medication, COUNT(*) as prescription_count
                    FROM clinical_data.medications m
                    WHERE m.reason_description ILIKE '%hypertension%'
                    GROUP BY m.description
                    ORDER BY prescription_count DESC
                """,
                'category': 'medication_analysis',
                'expected_performance': 0.5
            },
            {
                'nlq': "Show patient demographics by age group",
                'sql': """
                    SELECT 
                        CASE 
                            WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, birth_date)) < 18 THEN 'Under 18'
                            WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, birth_date)) BETWEEN 18 AND 30 THEN '18-30'
                            WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, birth_date)) BETWEEN 31 AND 50 THEN '31-50'
                            WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, birth_date)) BETWEEN 51 AND 70 THEN '51-70'
                            ELSE 'Over 70'
                        END as age_group,
                        gender,
                        COUNT(*) as patient_count
                    FROM clinical_data.patients
                    GROUP BY age_group, gender
                    ORDER BY age_group, gender
                """,
                'category': 'complex_aggregation',
                'expected_performance': 0.3
            },
            {
                'nlq': "Find patients with multiple chronic conditions",
                'sql': """
                    SELECT p.first_name, p.last_name, COUNT(DISTINCT c.description) as condition_count,
                           STRING_AGG(DISTINCT c.description, '; ') as conditions
                    FROM clinical_data.patients p
                    JOIN clinical_data.conditions c ON p.id = c.patient_id
                    WHERE c.description ILIKE ANY(ARRAY['%diabetes%', '%hypertension%', '%heart%', '%kidney%'])
                    GROUP BY p.id, p.first_name, p.last_name
                    HAVING COUNT(DISTINCT c.description) >= 2
                    ORDER BY condition_count DESC
                """,
                'category': 'complex_clinical',
                'expected_performance': 1.0
            },
            {
                'nlq': "What's the average cost per encounter by organization?",
                'sql': """
                    SELECT o.name as organization, 
                           COUNT(e.id) as total_encounters,
                           AVG(e.total_claim_cost) as avg_cost_per_encounter,
                           SUM(e.total_claim_cost) as total_cost
                    FROM clinical_data.organizations o
                    JOIN clinical_data.encounters e ON o.id = e.organization_id
                    WHERE e.total_claim_cost IS NOT NULL
                    GROUP BY o.id, o.name
                    ORDER BY avg_cost_per_encounter DESC
                """,
                'category': 'financial_analysis',
                'expected_performance': 0.8
            },
            {
                'nlq': "Show medication adherence patterns",
                'sql': """
                    SELECT m.description as medication,
                           COUNT(*) as total_prescriptions,
                           AVG(m.dispenses) as avg_dispenses,
                           AVG(EXTRACT(DAYS FROM (m.stop_date - m.start_date))) as avg_duration_days
                    FROM clinical_data.medications m
                    WHERE m.stop_date IS NOT NULL AND m.start_date IS NOT NULL
                    GROUP BY m.description
                    HAVING COUNT(*) >= 5
                    ORDER BY total_prescriptions DESC
                    LIMIT 15
                """,
                'category': 'temporal_analysis',
                'expected_performance': 0.7
            }
        ]
    
    def execute_query_with_timing(self, query: str, query_name: str) -> Dict:
        """Execute a query and measure performance"""
        try:
            with self.engine.connect() as conn:
                # Warm up query (execute once to load into cache)
                conn.execute(text(query))
                
                # Actual timed execution
                start_time = time.time()
                result = conn.execute(text(query))
                rows = result.fetchall()
                end_time = time.time()
                
                execution_time = end_time - start_time
                
                # Get column names
                columns = list(result.keys()) if hasattr(result, 'keys') else []
                
                return {
                    'success': True,
                    'execution_time': round(execution_time, 4),
                    'row_count': len(rows),
                    'columns': columns,
                    'sample_data': [dict(zip(columns, row)) for row in rows[:5]] if rows else []
                }
        
        except Exception as e:
            logger.error(f"Query {query_name} failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'execution_time': None,
                'row_count': 0
            }
    
    def run_query_tests(self) -> Dict:
        """Run all sample NLQ queries and measure performance"""
        logger.info("Running NLQ query performance tests...")
        
        query_results = {}
        total_queries = len(self.sample_queries)
        
        for i, query_test in enumerate(self.sample_queries, 1):
            logger.info(f"Testing query {i}/{total_queries}: {query_test['nlq']}")
            
            result = self.execute_query_with_timing(
                query_test['sql'], 
                f"query_{i}"
            )
            
            # Add test metadata
            result.update({
                'nlq': query_test['nlq'],
                'category': query_test['category'],
                'expected_performance': query_test['expected_performance'],
                'meets_expectation': (
                    result.get('execution_time', float('inf')) <= query_test['expected_performance']
                    if result.get('success', False) else False
                )
            })
            
            query_results[f"query_{i}_{query_test['category']}"] = result
            
            # Log result
            if result['success']:
                status = "✅" if result['meets_expectation'] else "⚠️"
                logger.info(f"  {status} {result['execution_time']}s ({result['row_count']} rows)")
            else:
                logger.error(f"  ❌ Failed: {result.get('error', 'Unknown error')}")
        
        self.test_results['query_tests'] = query_results
        return query_results
    
    def analyze_performance_patterns(self) -> Dict:
        """Analyze performance patterns across query categories"""
        logger.info("Analyzing performance patterns...")
        
        query_results = self.test_results.get('query_tests', {})
        
        # Group by category
        category_performance = {}
        
        for query_name, result in query_results.items():
            if not result.get('success', False):
                continue
                
            category = result.get('category', 'unknown')
            
            if category not in category_performance:
                category_performance[category] = {
                    'queries': [],
                    'total_time': 0,
                    'total_rows': 0,
                    'avg_time': 0,
                    'meets_expectations': 0,
                    'query_count': 0
                }
            
            cat_data = category_performance[category]
            cat_data['queries'].append(query_name)
            cat_data['total_time'] += result.get('execution_time', 0)
            cat_data['total_rows'] += result.get('row_count', 0)
            cat_data['query_count'] += 1
            
            if result.get('meets_expectation', False):
                cat_data['meets_expectations'] += 1
        
        # Calculate averages
        for category, data in category_performance.items():
            if data['query_count'] > 0:
                data['avg_time'] = round(data['total_time'] / data['query_count'], 4)
                data['success_rate'] = round((data['meets_expectations'] / data['query_count']) * 100, 1)
        
        # Overall statistics
        successful_queries = [r for r in query_results.values() if r.get('success', False)]
        
        overall_stats = {
            'total_queries': len(query_results),
            'successful_queries': len(successful_queries),
            'failed_queries': len(query_results) - len(successful_queries),
            'success_rate': round((len(successful_queries) / len(query_results)) * 100, 1) if query_results else 0,
            'avg_execution_time': round(
                sum(r.get('execution_time', 0) for r in successful_queries) / len(successful_queries), 4
            ) if successful_queries else 0,
            'total_rows_returned': sum(r.get('row_count', 0) for r in successful_queries),
            'queries_meeting_expectations': sum(1 for r in successful_queries if r.get('meets_expectation', False)),
            'expectation_success_rate': round(
                (sum(1 for r in successful_queries if r.get('meets_expectation', False)) / len(successful_queries)) * 100, 1
            ) if successful_queries else 0
        }
        
        performance_summary = {
            'overall_stats': overall_stats,
            'category_performance': category_performance
        }
        
        self.test_results['performance_summary'] = performance_summary
        return performance_summary
    
    def generate_sample_data_insights(self) -> Dict:
        """Generate insights from sample data returned by queries"""
        logger.info("Generating sample data insights...")
        
        insights = {
            'patient_demographics': {},
            'clinical_patterns': {},
            'data_distribution': {}
        }
        
        try:
            with self.engine.connect() as conn:
                # Patient demographics
                result = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_patients,
                        COUNT(CASE WHEN gender = 'F' THEN 1 END) as female_patients,
                        COUNT(CASE WHEN gender = 'M' THEN 1 END) as male_patients,
                        AVG(EXTRACT(YEAR FROM AGE(CURRENT_DATE, birth_date))) as avg_age,
                        MIN(birth_date) as oldest_birth_date,
                        MAX(birth_date) as youngest_birth_date
                    FROM clinical_data.patients
                """))
                
                row = result.fetchone()
                insights['patient_demographics'] = {
                    'total_patients': row[0],
                    'female_patients': row[1],
                    'male_patients': row[2],
                    'female_percentage': round((row[1] / row[0]) * 100, 1) if row[0] > 0 else 0,
                    'male_percentage': round((row[2] / row[0]) * 100, 1) if row[0] > 0 else 0,
                    'average_age': round(float(row[3]), 1) if row[3] else None,
                    'age_range': f"{row[4]} to {row[5]}" if row[4] and row[5] else None
                }
                
                # Clinical patterns
                result = conn.execute(text("""
                    SELECT 
                        COUNT(DISTINCT c.patient_id) as patients_with_conditions,
                        COUNT(DISTINCT c.description) as unique_conditions,
                        AVG(condition_count.count) as avg_conditions_per_patient
                    FROM clinical_data.conditions c
                    JOIN (
                        SELECT patient_id, COUNT(*) as count
                        FROM clinical_data.conditions
                        GROUP BY patient_id
                    ) condition_count ON c.patient_id = condition_count.patient_id
                """))
                
                row = result.fetchone()
                insights['clinical_patterns'] = {
                    'patients_with_conditions': row[0],
                    'unique_conditions': row[1],
                    'avg_conditions_per_patient': round(float(row[2]), 1) if row[2] else 0
                }
                
                # Data distribution
                result = conn.execute(text("""
                    SELECT 
                        'encounters' as table_name, COUNT(*) as record_count
                    FROM clinical_data.encounters
                    UNION ALL
                    SELECT 'conditions', COUNT(*) FROM clinical_data.conditions
                    UNION ALL
                    SELECT 'medications', COUNT(*) FROM clinical_data.medications
                    ORDER BY record_count DESC
                """))
                
                distribution = {row[0]: row[1] for row in result.fetchall()}
                insights['data_distribution'] = distribution
        
        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
            insights['error'] = str(e)
        
        self.test_results['sample_data'] = insights
        return insights
    
    def create_performance_indexes(self) -> Dict:
        """Create recommended indexes for better query performance"""
        logger.info("Creating performance indexes...")
        
        index_results = {
            'created_indexes': [],
            'failed_indexes': [],
            'recommendations': []
        }
        
        # Recommended indexes based on common query patterns
        recommended_indexes = [
            {
                'name': 'idx_patients_gender',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_patients_gender ON clinical_data.patients(gender)',
                'reason': 'Optimize gender-based filtering'
            },
            {
                'name': 'idx_conditions_patient_id',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_conditions_patient_id ON clinical_data.conditions(patient_id)',
                'reason': 'Optimize patient-condition joins'
            },
            {
                'name': 'idx_conditions_description',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_conditions_description ON clinical_data.conditions(description)',
                'reason': 'Optimize condition name searches'
            },
            {
                'name': 'idx_encounters_patient_id',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_encounters_patient_id ON clinical_data.encounters(patient_id)',
                'reason': 'Optimize patient-encounter joins'
            },
            {
                'name': 'idx_encounters_organization_id',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_encounters_organization_id ON clinical_data.encounters(organization_id)',
                'reason': 'Optimize organization-based queries'
            },
            {
                'name': 'idx_medications_patient_id',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_medications_patient_id ON clinical_data.medications(patient_id)',
                'reason': 'Optimize patient-medication joins'
            },
            {
                'name': 'idx_medications_reason_description',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_medications_reason_description ON clinical_data.medications(reason_description)',
                'reason': 'Optimize medication reason searches'
            }
        ]
        
        try:
            with self.engine.connect() as conn:
                for index in recommended_indexes:
                    try:
                        conn.execute(text(index['sql']))
                        conn.commit()
                        index_results['created_indexes'].append({
                            'name': index['name'],
                            'reason': index['reason']
                        })
                        logger.info(f"✅ Created index: {index['name']}")
                    
                    except Exception as e:
                        index_results['failed_indexes'].append({
                            'name': index['name'],
                            'error': str(e)
                        })
                        logger.warning(f"⚠️ Failed to create index {index['name']}: {e}")
        
        except Exception as e:
            logger.error(f"Index creation failed: {e}")
            index_results['error'] = str(e)
        
        return index_results
    
    def save_test_report(self, output_path=None) -> str:
        """Save comprehensive test report"""
        if output_path is None:
            output_path = Path(r'd:\projects\healthca\docs') / 'nlq_performance_report.json'
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        logger.info(f"Test report saved to: {output_path}")
        return str(output_path)
    
    def generate_markdown_report(self, output_path=None) -> str:
        """Generate human-readable markdown report"""
        if output_path is None:
            output_path = Path(r'd:\projects\healthca\docs') / 'nlq_performance_report.md'
        
        performance = self.test_results.get('performance_summary', {})
        overall_stats = performance.get('overall_stats', {})
        
        report_lines = [
            "# NLQ Query Performance Test Report",
            f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "## Executive Summary",
            f"- **Total Queries Tested**: {overall_stats.get('total_queries', 0)}",
            f"- **Success Rate**: {overall_stats.get('success_rate', 0)}%",
            f"- **Average Execution Time**: {overall_stats.get('avg_execution_time', 0)}s",
            f"- **Queries Meeting Performance Expectations**: {overall_stats.get('expectation_success_rate', 0)}%",
            f"- **Total Rows Returned**: {overall_stats.get('total_rows_returned', 0):,}",
            "",
            "## Query Performance by Category",
            "",
            "| Category | Queries | Avg Time (s) | Success Rate | Total Rows |",
            "|----------|---------|--------------|--------------|------------|"
        ]
        
        category_performance = performance.get('category_performance', {})
        for category, data in category_performance.items():
            report_lines.append(
                f"| {category} | {data['query_count']} | {data['avg_time']} | {data['success_rate']}% | {data['total_rows']:,} |"
            )
        
        # Add detailed query results
        report_lines.extend([
            "",
            "## Detailed Query Results",
            ""
        ])
        
        query_tests = self.test_results.get('query_tests', {})
        for query_name, result in query_tests.items():
            status = "✅" if result.get('success', False) else "❌"
            performance_status = "🚀" if result.get('meets_expectation', False) else "⚠️"
            
            report_lines.extend([
                f"### {query_name}",
                f"**Natural Language**: {result.get('nlq', 'N/A')}",
                f"**Status**: {status} **Performance**: {performance_status}",
                f"**Execution Time**: {result.get('execution_time', 'N/A')}s",
                f"**Rows Returned**: {result.get('row_count', 0):,}",
                f"**Category**: {result.get('category', 'N/A')}",
                ""
            ])
        
        # Add sample data insights
        sample_data = self.test_results.get('sample_data', {})
        if sample_data:
            report_lines.extend([
                "## Database Insights",
                "",
                "### Patient Demographics"
            ])
            
            demographics = sample_data.get('patient_demographics', {})
            for key, value in demographics.items():
                if key != 'error':
                    report_lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
        
        # Save report
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        logger.info(f"Markdown report saved to: {output_path}")
        return str(output_path)
    
    def run_comprehensive_tests(self) -> bool:
        """Run all NLQ performance tests"""
        logger.info("Starting comprehensive NLQ query testing...")
        
        try:
            # Create performance indexes first
            logger.info("Creating performance indexes...")
            index_results = self.create_performance_indexes()
            
            # Run query tests
            query_results = self.run_query_tests()
            
            # Analyze performance patterns
            performance_analysis = self.analyze_performance_patterns()
            
            # Generate sample data insights
            data_insights = self.generate_sample_data_insights()
            
            # Save reports
            json_report = self.save_test_report()
            md_report = self.generate_markdown_report()
            
            # Final summary
            overall_stats = performance_analysis.get('overall_stats', {})
            logger.info("=" * 60)
            logger.info("NLQ QUERY TESTING COMPLETE")
            logger.info("=" * 60)
            logger.info(f"Total Queries: {overall_stats.get('total_queries', 0)}")
            logger.info(f"Success Rate: {overall_stats.get('success_rate', 0)}%")
            logger.info(f"Average Execution Time: {overall_stats.get('avg_execution_time', 0)}s")
            logger.info(f"Performance Expectation Rate: {overall_stats.get('expectation_success_rate', 0)}%")
            logger.info(f"Indexes Created: {len(index_results.get('created_indexes', []))}")
            logger.info(f"JSON Report: {json_report}")
            logger.info(f"Markdown Report: {md_report}")
            logger.info("=" * 60)
            
            return overall_stats.get('success_rate', 0) >= 80
        
        except Exception as e:
            logger.error(f"Comprehensive testing failed: {e}")
            return False

def main():
    """Main execution function"""
    tester = NLQQueryTester()
    success = tester.run_comprehensive_tests()
    return success

if __name__ == "__main__":
    main()