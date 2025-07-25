#!/usr/bin/env python3
"""
Analyze Synthea Dataset Structure
Comprehensive analysis of all CSV files to understand data structure, relationships, and quality
"""

import os
import pandas as pd
import numpy as np
import logging
from pathlib import Path
import json
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SyntheaStructureAnalyzer:
    def __init__(self, csv_dir=r'd:\projects\healthca\output\csv'):
        self.csv_dir = Path(csv_dir)
        self.analysis_results = {}
        self.relationships = {}
        
    def analyze_csv_file(self, csv_path):
        """Analyze individual CSV file structure and content"""
        try:
            logger.info(f"Analyzing {csv_path.name}...")
            
            # Read CSV with sample to understand structure
            df = pd.read_csv(csv_path, low_memory=False, nrows=1000)  # Sample first 1000 rows
            
            analysis = {
                'file_name': csv_path.name,
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'columns': {},
                'data_types': {},
                'missing_values': {},
                'unique_values': {},
                'sample_data': {}
            }
            
            # Analyze each column
            for col in df.columns:
                col_data = df[col]
                
                analysis['columns'][col] = {
                    'dtype': str(col_data.dtype),
                    'non_null_count': col_data.count(),
                    'null_count': col_data.isnull().sum(),
                    'null_percentage': (col_data.isnull().sum() / len(col_data)) * 100,
                    'unique_count': col_data.nunique(),
                    'unique_percentage': (col_data.nunique() / len(col_data)) * 100 if len(col_data) > 0 else 0
                }
                
                # Sample values (first 5 non-null values)
                sample_values = col_data.dropna().head(5).tolist()
                analysis['sample_data'][col] = sample_values
                
                # Detect potential ID columns (UUID format)
                if col_data.dtype == 'object' and col_data.str.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', na=False).any():
                    analysis['columns'][col]['is_uuid'] = True
                    analysis['columns'][col]['potential_key'] = True
                else:
                    analysis['columns'][col]['is_uuid'] = False
                    analysis['columns'][col]['potential_key'] = False
                
                # Detect date columns
                if 'date' in col.lower() or 'time' in col.lower():
                    try:
                        pd.to_datetime(col_data.dropna().head(10))
                        analysis['columns'][col]['is_date'] = True
                    except:
                        analysis['columns'][col]['is_date'] = False
                else:
                    analysis['columns'][col]['is_date'] = False
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing {csv_path.name}: {e}")
            return None
    
    def identify_relationships(self):
        """Identify potential foreign key relationships between tables"""
        logger.info("Identifying relationships between tables...")
        
        # Common relationship patterns
        relationship_patterns = {
            'patient': ['patient', 'patient_id'],
            'encounter': ['encounter', 'encounter_id'],
            'organization': ['organization', 'organization_id'],
            'provider': ['provider', 'provider_id'],
            'payer': ['payer', 'payer_id']
        }
        
        relationships = {}
        
        for table_name, analysis in self.analysis_results.items():
            if analysis is None:
                continue
                
            table_relationships = []
            
            for col_name, col_info in analysis['columns'].items():
                col_lower = col_name.lower()
                
                # Check for UUID columns that might be foreign keys
                if col_info.get('is_uuid', False):
                    for entity, patterns in relationship_patterns.items():
                        if any(pattern in col_lower for pattern in patterns):
                            table_relationships.append({
                                'column': col_name,
                                'references_table': entity,
                                'relationship_type': 'foreign_key'
                            })
            
            relationships[table_name] = table_relationships
        
        self.relationships = relationships
        return relationships
    
    def generate_erd_data(self):
        """Generate data for Entity-Relationship Diagram"""
        logger.info("Generating ERD data...")
        
        erd_data = {
            'entities': {},
            'relationships': []
        }
        
        # Process entities (tables)
        for table_name, analysis in self.analysis_results.items():
            if analysis is None:
                continue
                
            entity_name = table_name.replace('.csv', '')
            
            # Identify primary key
            primary_key = None
            for col_name, col_info in analysis['columns'].items():
                if col_name.lower() in ['id', 'uuid'] and col_info.get('is_uuid', False):
                    primary_key = col_name
                    break
            
            # Categorize columns
            columns = []
            foreign_keys = []
            
            for col_name, col_info in analysis['columns'].items():
                col_type = self._map_data_type(col_info['dtype'])
                
                column_data = {
                    'name': col_name,
                    'type': col_type,
                    'nullable': col_info['null_count'] > 0,
                    'unique': col_info['unique_percentage'] > 95
                }
                
                if col_name == primary_key:
                    column_data['primary_key'] = True
                
                # Check if it's a foreign key
                if col_info.get('is_uuid', False) and col_name != primary_key:
                    column_data['foreign_key'] = True
                    foreign_keys.append(col_name)
                
                columns.append(column_data)
            
            erd_data['entities'][entity_name] = {
                'columns': columns,
                'primary_key': primary_key,
                'foreign_keys': foreign_keys,
                'row_count': analysis['total_rows']
            }
        
        # Process relationships
        for table_name, table_relationships in self.relationships.items():
            entity_name = table_name.replace('.csv', '')
            
            for rel in table_relationships:
                erd_data['relationships'].append({
                    'from_table': entity_name,
                    'from_column': rel['column'],
                    'to_table': rel['references_table'],
                    'to_column': 'id',  # Assuming standard ID column
                    'relationship_type': rel['relationship_type']
                })
        
        return erd_data
    
    def _map_data_type(self, pandas_dtype):
        """Map pandas data types to SQL data types"""
        dtype_mapping = {
            'object': 'VARCHAR',
            'int64': 'INTEGER',
            'float64': 'DECIMAL',
            'bool': 'BOOLEAN',
            'datetime64[ns]': 'TIMESTAMP'
        }
        return dtype_mapping.get(str(pandas_dtype), 'VARCHAR')
    
    def analyze_all_files(self):
        """Analyze all CSV files in the directory"""
        logger.info(f"Starting analysis of CSV files in {self.csv_dir}")
        
        csv_files = list(self.csv_dir.glob('*.csv'))
        logger.info(f"Found {len(csv_files)} CSV files")
        
        for csv_file in csv_files:
            analysis = self.analyze_csv_file(csv_file)
            if analysis:
                self.analysis_results[csv_file.name] = analysis
        
        # Identify relationships
        self.identify_relationships()
        
        return self.analysis_results
    
    def generate_report(self, output_path=None):
        """Generate comprehensive analysis report"""
        if output_path is None:
            output_path = self.csv_dir.parent / 'docs' / 'synthea_structure_analysis.md'
        
        logger.info(f"Generating analysis report: {output_path}")
        
        report_lines = [
            "# Synthea Dataset Structure Analysis",
            f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "## Overview",
            f"- **Total CSV Files**: {len(self.analysis_results)}",
            f"- **Analysis Date**: {datetime.now().strftime('%Y-%m-%d')}",
            "",
            "## File Summary",
            ""
        ]
        
        # Summary table
        report_lines.extend([
            "| File | Rows | Columns | Key Columns | Missing Data |",
            "|------|------|---------|-------------|--------------|"
        ])
        
        for file_name, analysis in self.analysis_results.items():
            if analysis is None:
                continue
                
            key_cols = [col for col, info in analysis['columns'].items() 
                       if info.get('potential_key', False)]
            key_cols_str = ', '.join(key_cols[:3]) + ('...' if len(key_cols) > 3 else '')
            
            total_missing = sum(info['null_count'] for info in analysis['columns'].values())
            missing_pct = (total_missing / (analysis['total_rows'] * analysis['total_columns'])) * 100
            
            report_lines.append(
                f"| {file_name} | {analysis['total_rows']:,} | {analysis['total_columns']} | "
                f"{key_cols_str} | {missing_pct:.1f}% |"
            )
        
        report_lines.extend(["", "## Detailed Analysis", ""])
        
        # Detailed analysis for each file
        for file_name, analysis in self.analysis_results.items():
            if analysis is None:
                continue
                
            entity_name = file_name.replace('.csv', '')
            report_lines.extend([
                f"### {entity_name.title()}",
                f"**File**: `{file_name}`",
                f"**Rows**: {analysis['total_rows']:,}",
                f"**Columns**: {analysis['total_columns']}",
                "",
                "#### Column Details",
                "| Column | Type | Null % | Unique % | Sample Values |",
                "|--------|------|--------|----------|---------------|"
            ])
            
            for col_name, col_info in analysis['columns'].items():
                sample_vals = analysis['sample_data'].get(col_name, [])
                sample_str = ', '.join(str(v)[:20] for v in sample_vals[:3])
                if len(sample_str) > 50:
                    sample_str = sample_str[:47] + "..."
                
                report_lines.append(
                    f"| {col_name} | {col_info['dtype']} | {col_info['null_percentage']:.1f}% | "
                    f"{col_info['unique_percentage']:.1f}% | {sample_str} |"
                )
            
            report_lines.extend(["", ""])
        
        # Relationships section
        report_lines.extend([
            "## Identified Relationships",
            ""
        ])
        
        for table_name, relationships in self.relationships.items():
            if relationships:
                entity_name = table_name.replace('.csv', '')
                report_lines.append(f"### {entity_name.title()}")
                for rel in relationships:
                    report_lines.append(
                        f"- `{rel['column']}` → `{rel['references_table']}.id` ({rel['relationship_type']})"
                    )
                report_lines.append("")
        
        # Write report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        logger.info(f"Analysis report saved to: {output_path}")
        return output_path
    
    def save_erd_data(self, output_path=None):
        """Save ERD data as JSON for diagram generation"""
        if output_path is None:
            output_path = self.csv_dir.parent / 'docs' / 'synthea_erd_data.json'
        
        erd_data = self.generate_erd_data()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(erd_data, f, indent=2, default=str)
        
        logger.info(f"ERD data saved to: {output_path}")
        return output_path

def main():
    """Main execution function"""
    analyzer = SyntheaStructureAnalyzer()
    
    # Analyze all files
    results = analyzer.analyze_all_files()
    
    # Generate reports
    report_path = analyzer.generate_report()
    erd_path = analyzer.save_erd_data()
    
    logger.info("=" * 60)
    logger.info("SYNTHEA STRUCTURE ANALYSIS COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Files analyzed: {len(results)}")
    logger.info(f"Analysis report: {report_path}")
    logger.info(f"ERD data: {erd_path}")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()