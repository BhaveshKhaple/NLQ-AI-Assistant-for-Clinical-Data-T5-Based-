#!/usr/bin/env python3
"""
Result Formatter
Formats query results into various output formats (tables, JSON, CSV, etc.) for different interfaces.
"""

import json
import csv
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, date
from decimal import Decimal
import pandas as pd
from io import StringIO
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResultFormatter:
    """
    Formats database query results into various output formats.
    Supports tables, JSON, CSV, and custom formats for different UI components.
    """
    
    def __init__(self, config_path: str = "d:/projects/healthca/config/config.yaml"):
        """
        Initialize the result formatter.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.formatting_stats = {
            'total_formats': 0,
            'formats_by_type': {},
            'total_rows_formatted': 0,
            'avg_formatting_time': 0.0
        }
        
        logger.info("🎨 Result Formatter initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"✅ Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            # Return default config
            return {
                'ui': {
                    'results_per_page': 50,
                    'show_sql': True
                },
                'performance': {
                    'max_export_rows': 10000
                }
            }
    
    def _serialize_value(self, value: Any) -> Any:
        """
        Serialize complex data types for JSON output.
        
        Args:
            value: Value to serialize
            
        Returns:
            Serialized value
        """
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        elif isinstance(value, Decimal):
            return float(value)
        elif hasattr(value, '__dict__'):
            return str(value)
        else:
            return value
    
    def format_as_table(self, 
                       query_result: Dict[str, Any], 
                       max_rows: Optional[int] = None,
                       include_metadata: bool = True) -> Dict[str, Any]:
        """
        Format query results as a structured table format.
        
        Args:
            query_result: Result from DatabaseExecutor
            max_rows: Maximum number of rows to include
            include_metadata: Whether to include query metadata
            
        Returns:
            Dict with formatted table data
        """
        try:
            if not query_result.get('success', False):
                return {
                    'success': False,
                    'error': query_result.get('error', 'Unknown error'),
                    'error_type': query_result.get('error_type', 'UNKNOWN'),
                    'format': 'table'
                }
            
            data = query_result.get('data', [])
            columns = query_result.get('columns', [])
            
            # Apply row limit
            max_rows = max_rows or self.config.get('ui', {}).get('results_per_page', 50)
            if len(data) > max_rows:
                data = data[:max_rows]
                truncated = True
            else:
                truncated = query_result.get('truncated', False)
            
            # Serialize data for JSON compatibility
            serialized_data = []
            for row in data:
                serialized_row = {}
                for key, value in row.items():
                    serialized_row[key] = self._serialize_value(value)
                serialized_data.append(serialized_row)
            
            # Format column information
            formatted_columns = []
            for col in columns:
                formatted_columns.append({
                    'name': col.get('name', ''),
                    'type': col.get('type', 'unknown'),
                    'nullable': col.get('nullable', True),
                    'display_name': col.get('name', '').replace('_', ' ').title()
                })
            
            result = {
                'success': True,
                'format': 'table',
                'data': serialized_data,
                'columns': formatted_columns,
                'row_count': len(serialized_data),
                'total_rows': query_result.get('rows_returned', len(serialized_data)),
                'truncated': truncated,
                'pagination': {
                    'current_page': 1,
                    'page_size': max_rows,
                    'has_more': truncated
                }
            }
            
            # Include metadata if requested
            if include_metadata:
                result['metadata'] = {
                    'query_id': query_result.get('query_id'),
                    'execution_time': query_result.get('execution_time', 0),
                    'sql': query_result.get('sql', '') if self.config.get('ui', {}).get('show_sql', True) else None,
                    'timestamp': datetime.now().isoformat(),
                    'security_check': query_result.get('security_check', {})
                }
            
            # Update statistics
            self.formatting_stats['total_formats'] += 1
            self.formatting_stats['formats_by_type']['table'] = (
                self.formatting_stats['formats_by_type'].get('table', 0) + 1
            )
            self.formatting_stats['total_rows_formatted'] += len(serialized_data)
            
            logger.info(f"✅ Formatted {len(serialized_data)} rows as table")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error formatting as table: {e}")
            return {
                'success': False,
                'error': f"Formatting error: {str(e)}",
                'format': 'table'
            }
    
    def format_as_json(self, 
                      query_result: Dict[str, Any], 
                      pretty: bool = True,
                      include_metadata: bool = True) -> Dict[str, Any]:
        """
        Format query results as JSON.
        
        Args:
            query_result: Result from DatabaseExecutor
            pretty: Whether to format JSON with indentation
            include_metadata: Whether to include query metadata
            
        Returns:
            Dict with JSON formatted data
        """
        try:
            if not query_result.get('success', False):
                return {
                    'success': False,
                    'error': query_result.get('error', 'Unknown error'),
                    'error_type': query_result.get('error_type', 'UNKNOWN'),
                    'format': 'json'
                }
            
            data = query_result.get('data', [])
            
            # Serialize data
            serialized_data = []
            for row in data:
                serialized_row = {}
                for key, value in row.items():
                    serialized_row[key] = self._serialize_value(value)
                serialized_data.append(serialized_row)
            
            # Create JSON structure
            json_result = {
                'data': serialized_data,
                'row_count': len(serialized_data),
                'columns': [col.get('name', '') for col in query_result.get('columns', [])]
            }
            
            # Include metadata if requested
            if include_metadata:
                json_result['metadata'] = {
                    'query_id': query_result.get('query_id'),
                    'execution_time': query_result.get('execution_time', 0),
                    'timestamp': datetime.now().isoformat(),
                    'truncated': query_result.get('truncated', False)
                }
                
                if self.config.get('ui', {}).get('show_sql', True):
                    json_result['metadata']['sql'] = query_result.get('sql', '')
            
            # Convert to JSON string
            indent = 2 if pretty else None
            json_string = json.dumps(json_result, indent=indent, ensure_ascii=False)
            
            result = {
                'success': True,
                'format': 'json',
                'json_string': json_string,
                'json_object': json_result,
                'size_bytes': len(json_string.encode('utf-8'))
            }
            
            # Update statistics
            self.formatting_stats['total_formats'] += 1
            self.formatting_stats['formats_by_type']['json'] = (
                self.formatting_stats['formats_by_type'].get('json', 0) + 1
            )
            self.formatting_stats['total_rows_formatted'] += len(serialized_data)
            
            logger.info(f"✅ Formatted {len(serialized_data)} rows as JSON ({result['size_bytes']} bytes)")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error formatting as JSON: {e}")
            return {
                'success': False,
                'error': f"JSON formatting error: {str(e)}",
                'format': 'json'
            }
    
    def format_as_csv(self, 
                     query_result: Dict[str, Any], 
                     delimiter: str = ',',
                     include_headers: bool = True) -> Dict[str, Any]:
        """
        Format query results as CSV.
        
        Args:
            query_result: Result from DatabaseExecutor
            delimiter: CSV delimiter character
            include_headers: Whether to include column headers
            
        Returns:
            Dict with CSV formatted data
        """
        try:
            if not query_result.get('success', False):
                return {
                    'success': False,
                    'error': query_result.get('error', 'Unknown error'),
                    'error_type': query_result.get('error_type', 'UNKNOWN'),
                    'format': 'csv'
                }
            
            data = query_result.get('data', [])
            columns = query_result.get('columns', [])
            
            if not data:
                return {
                    'success': True,
                    'format': 'csv',
                    'csv_string': '',
                    'row_count': 0
                }
            
            # Create CSV string
            output = StringIO()
            
            # Get column names
            column_names = [col.get('name', '') for col in columns] if columns else list(data[0].keys())
            
            writer = csv.DictWriter(
                output, 
                fieldnames=column_names, 
                delimiter=delimiter,
                quoting=csv.QUOTE_MINIMAL,
                lineterminator='\n'
            )
            
            # Write headers if requested
            if include_headers:
                writer.writeheader()
            
            # Write data rows
            for row in data:
                # Serialize values for CSV
                csv_row = {}
                for key, value in row.items():
                    if key in column_names:
                        csv_row[key] = self._serialize_value(value)
                writer.writerow(csv_row)
            
            csv_string = output.getvalue()
            output.close()
            
            result = {
                'success': True,
                'format': 'csv',
                'csv_string': csv_string,
                'row_count': len(data),
                'column_count': len(column_names),
                'size_bytes': len(csv_string.encode('utf-8')),
                'delimiter': delimiter,
                'has_headers': include_headers
            }
            
            # Update statistics
            self.formatting_stats['total_formats'] += 1
            self.formatting_stats['formats_by_type']['csv'] = (
                self.formatting_stats['formats_by_type'].get('csv', 0) + 1
            )
            self.formatting_stats['total_rows_formatted'] += len(data)
            
            logger.info(f"✅ Formatted {len(data)} rows as CSV ({result['size_bytes']} bytes)")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error formatting as CSV: {e}")
            return {
                'success': False,
                'error': f"CSV formatting error: {str(e)}",
                'format': 'csv'
            }
    
    def format_as_dataframe(self, query_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format query results as pandas DataFrame.
        
        Args:
            query_result: Result from DatabaseExecutor
            
        Returns:
            Dict with DataFrame and metadata
        """
        try:
            if not query_result.get('success', False):
                return {
                    'success': False,
                    'error': query_result.get('error', 'Unknown error'),
                    'error_type': query_result.get('error_type', 'UNKNOWN'),
                    'format': 'dataframe'
                }
            
            data = query_result.get('data', [])
            
            if not data:
                df = pd.DataFrame()
            else:
                # Serialize data for DataFrame
                serialized_data = []
                for row in data:
                    serialized_row = {}
                    for key, value in row.items():
                        serialized_row[key] = self._serialize_value(value)
                    serialized_data.append(serialized_row)
                
                df = pd.DataFrame(serialized_data)
            
            # Get DataFrame info
            df_info = {
                'shape': df.shape,
                'columns': df.columns.tolist(),
                'dtypes': df.dtypes.to_dict(),
                'memory_usage': df.memory_usage(deep=True).sum(),
                'null_counts': df.isnull().sum().to_dict()
            }
            
            result = {
                'success': True,
                'format': 'dataframe',
                'dataframe': df,
                'info': df_info,
                'row_count': len(df),
                'column_count': len(df.columns)
            }
            
            # Update statistics
            self.formatting_stats['total_formats'] += 1
            self.formatting_stats['formats_by_type']['dataframe'] = (
                self.formatting_stats['formats_by_type'].get('dataframe', 0) + 1
            )
            self.formatting_stats['total_rows_formatted'] += len(df)
            
            logger.info(f"✅ Formatted {len(df)} rows as DataFrame ({df.shape})")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error formatting as DataFrame: {e}")
            return {
                'success': False,
                'error': f"DataFrame formatting error: {str(e)}",
                'format': 'dataframe'
            }
    
    def format_for_streamlit(self, query_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format query results specifically for Streamlit display.
        
        Args:
            query_result: Result from DatabaseExecutor
            
        Returns:
            Dict with Streamlit-optimized format
        """
        try:
            if not query_result.get('success', False):
                return {
                    'success': False,
                    'error': query_result.get('error', 'Unknown error'),
                    'error_type': query_result.get('error_type', 'UNKNOWN'),
                    'format': 'streamlit'
                }
            
            # Get DataFrame format first
            df_result = self.format_as_dataframe(query_result)
            if not df_result.get('success', False):
                return df_result
            
            df = df_result['dataframe']
            
            # Create summary statistics for numeric columns
            numeric_summary = {}
            for col in df.select_dtypes(include=['number']).columns:
                numeric_summary[col] = {
                    'count': int(df[col].count()),
                    'mean': float(df[col].mean()) if not df[col].empty else 0,
                    'std': float(df[col].std()) if not df[col].empty else 0,
                    'min': float(df[col].min()) if not df[col].empty else 0,
                    'max': float(df[col].max()) if not df[col].empty else 0
                }
            
            # Create categorical summary
            categorical_summary = {}
            for col in df.select_dtypes(include=['object', 'category']).columns:
                value_counts = df[col].value_counts().head(10)
                categorical_summary[col] = {
                    'unique_count': int(df[col].nunique()),
                    'top_values': value_counts.to_dict()
                }
            
            result = {
                'success': True,
                'format': 'streamlit',
                'dataframe': df,
                'display_data': df.to_dict('records'),
                'columns': df.columns.tolist(),
                'row_count': len(df),
                'column_count': len(df.columns),
                'summary': {
                    'numeric': numeric_summary,
                    'categorical': categorical_summary,
                    'null_counts': df.isnull().sum().to_dict(),
                    'data_types': df.dtypes.astype(str).to_dict()
                },
                'metadata': {
                    'query_id': query_result.get('query_id'),
                    'execution_time': query_result.get('execution_time', 0),
                    'timestamp': datetime.now().isoformat(),
                    'truncated': query_result.get('truncated', False)
                }
            }
            
            # Include SQL if configured
            if self.config.get('ui', {}).get('show_sql', True):
                result['metadata']['sql'] = query_result.get('sql', '')
            
            # Update statistics
            self.formatting_stats['total_formats'] += 1
            self.formatting_stats['formats_by_type']['streamlit'] = (
                self.formatting_stats['formats_by_type'].get('streamlit', 0) + 1
            )
            self.formatting_stats['total_rows_formatted'] += len(df)
            
            logger.info(f"✅ Formatted {len(df)} rows for Streamlit display")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error formatting for Streamlit: {e}")
            return {
                'success': False,
                'error': f"Streamlit formatting error: {str(e)}",
                'format': 'streamlit'
            }
    
    def format_summary_stats(self, query_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate summary statistics for query results.
        
        Args:
            query_result: Result from DatabaseExecutor
            
        Returns:
            Dict with summary statistics
        """
        try:
            if not query_result.get('success', False):
                return {
                    'success': False,
                    'error': query_result.get('error', 'Unknown error')
                }
            
            data = query_result.get('data', [])
            
            if not data:
                return {
                    'success': True,
                    'summary': {
                        'row_count': 0,
                        'column_count': 0,
                        'data_types': {},
                        'null_counts': {},
                        'unique_counts': {}
                    }
                }
            
            # Convert to DataFrame for analysis
            df_result = self.format_as_dataframe(query_result)
            if not df_result.get('success', False):
                return df_result
            
            df = df_result['dataframe']
            
            # Generate comprehensive summary
            summary = {
                'row_count': len(df),
                'column_count': len(df.columns),
                'data_types': df.dtypes.astype(str).to_dict(),
                'null_counts': df.isnull().sum().to_dict(),
                'null_percentages': (df.isnull().sum() / len(df) * 100).to_dict(),
                'unique_counts': df.nunique().to_dict(),
                'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024
            }
            
            # Numeric column statistics
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                summary['numeric_stats'] = df[numeric_cols].describe().to_dict()
            
            # Categorical column statistics
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns
            if len(categorical_cols) > 0:
                summary['categorical_stats'] = {}
                for col in categorical_cols:
                    value_counts = df[col].value_counts().head(10)
                    summary['categorical_stats'][col] = {
                        'unique_count': int(df[col].nunique()),
                        'most_common': value_counts.to_dict(),
                        'mode': df[col].mode().iloc[0] if not df[col].mode().empty else None
                    }
            
            result = {
                'success': True,
                'format': 'summary',
                'summary': summary,
                'metadata': {
                    'query_id': query_result.get('query_id'),
                    'execution_time': query_result.get('execution_time', 0),
                    'analysis_timestamp': datetime.now().isoformat()
                }
            }
            
            logger.info(f"✅ Generated summary statistics for {len(df)} rows, {len(df.columns)} columns")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error generating summary statistics: {e}")
            return {
                'success': False,
                'error': f"Summary statistics error: {str(e)}",
                'format': 'summary'
            }
    
    def format_multiple(self, 
                       query_result: Dict[str, Any], 
                       formats: List[str],
                       **format_kwargs) -> Dict[str, Any]:
        """
        Format query results in multiple formats simultaneously.
        
        Args:
            query_result: Result from DatabaseExecutor
            formats: List of format types ('table', 'json', 'csv', 'dataframe', 'streamlit', 'summary')
            **format_kwargs: Additional arguments for specific formatters
            
        Returns:
            Dict with results in all requested formats
        """
        results = {
            'success': True,
            'formats': {},
            'metadata': {
                'requested_formats': formats,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        format_methods = {
            'table': self.format_as_table,
            'json': self.format_as_json,
            'csv': self.format_as_csv,
            'dataframe': self.format_as_dataframe,
            'streamlit': self.format_for_streamlit,
            'summary': self.format_summary_stats
        }
        
        for format_type in formats:
            if format_type in format_methods:
                try:
                    logger.info(f"🔄 Formatting as {format_type}")
                    format_result = format_methods[format_type](query_result, **format_kwargs)
                    results['formats'][format_type] = format_result
                    
                    if not format_result.get('success', False):
                        results['success'] = False
                        
                except Exception as e:
                    logger.error(f"❌ Error formatting as {format_type}: {e}")
                    results['formats'][format_type] = {
                        'success': False,
                        'error': str(e),
                        'format': format_type
                    }
                    results['success'] = False
            else:
                logger.warning(f"⚠️ Unknown format type: {format_type}")
                results['formats'][format_type] = {
                    'success': False,
                    'error': f"Unknown format type: {format_type}",
                    'format': format_type
                }
                results['success'] = False
        
        logger.info(f"✅ Multi-format processing completed: {len(formats)} formats")
        return results
    
    def get_formatting_stats(self) -> Dict[str, Any]:
        """Get formatting statistics."""
        return self.formatting_stats.copy()
    
    def reset_stats(self):
        """Reset formatting statistics."""
        self.formatting_stats = {
            'total_formats': 0,
            'formats_by_type': {},
            'total_rows_formatted': 0,
            'avg_formatting_time': 0.0
        }
        logger.info("📊 Formatting statistics reset")