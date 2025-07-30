#!/usr/bin/env python3
"""
Clinical NLQ Streamlit Web Interface
Main Streamlit application for the Clinical Natural Language Query Assistant.
"""

import os
import sys
import time
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Add src to path for imports if not already added
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from nlq.inference_pipeline import InferencePipeline
from ui.session_manager import SessionManager
from ui.activity_logger import ActivityLogger
from ui.ui_components import UIComponents
from ui.error_handler import UIErrorHandler
from ui.database_explorer import DatabaseExplorer

# Page configuration
st.set_page_config(
    page_title="Clinical NLQ Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/clinical-nlq',
        'Report a bug': 'https://github.com/your-repo/clinical-nlq/issues',
        'About': "Clinical Natural Language Query Assistant - Convert natural language to SQL queries for clinical data analysis."
    }
)

class ClinicalNLQApp:
    """Main Streamlit application class."""
    
    def __init__(self):
        """Initialize the application."""
        self.session_manager = SessionManager()
        self.activity_logger = ActivityLogger()
        self.ui_components = UIComponents()
        self.error_handler = UIErrorHandler()
        self.database_explorer = DatabaseExplorer()
        
        # Initialize session state
        self._initialize_session_state()
        
        # Initialize pipeline (cached)
        self.pipeline = self._get_pipeline()
    
    def _initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        if 'session_id' not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.session_start = datetime.now()
            st.session_state.query_history = []
            st.session_state.pipeline_initialized = False
            st.session_state.user_preferences = {
                'show_sql': True,
                'show_metadata': False,
                'default_format': 'table',
                'max_rows_display': 50
            }
            st.session_state.error_count = 0
            st.session_state.success_count = 0
    
    @st.cache_resource
    def _get_pipeline(_self):
        """Get or create the inference pipeline (cached)."""
        try:
            # Set database password if not set
            if not os.getenv('DB_PASSWORD'):
                os.environ['DB_PASSWORD'] = ''
            
            pipeline = InferencePipeline(auto_connect=False)
            return pipeline
        except Exception as e:
            st.error(f"Failed to create pipeline: {e}")
            return None
    
    def _initialize_pipeline(self):
        """Initialize the pipeline if not already done."""
        if not st.session_state.pipeline_initialized and self.pipeline:
            with st.spinner("🚀 Initializing Clinical NLQ Pipeline..."):
                try:
                    init_result = self.pipeline.initialize()
                    if init_result['success']:
                        st.session_state.pipeline_initialized = True
                        st.success(f"✅ Pipeline initialized successfully in {init_result['initialization_time']:.2f}s")
                        
                        # Log initialization
                        self.activity_logger.log_activity(
                            session_id=st.session_state.session_id,
                            activity_type='pipeline_init',
                            details={'initialization_time': init_result['initialization_time']},
                            success=True
                        )
                    else:
                        st.error(f"❌ Pipeline initialization failed: {init_result.get('error', 'Unknown error')}")
                        self.error_handler.handle_error(
                            error=init_result.get('error', 'Pipeline initialization failed'),
                            context={'component': 'pipeline_initialization'}
                        )
                        return False
                except Exception as e:
                    st.error(f"❌ Pipeline initialization error: {e}")
                    self.error_handler.handle_error(error=str(e), context={'component': 'pipeline_initialization'})
                    return False
        
        return st.session_state.pipeline_initialized
    
    def render_header(self):
        """Render the application header."""
        st.title("🏥 Clinical Natural Language Query Assistant")
        st.markdown("---")
        
        # Status indicators
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.session_state.pipeline_initialized:
                st.success("🟢 Pipeline Ready")
            else:
                st.warning("🟡 Pipeline Initializing")
        
        with col2:
            session_duration = datetime.now() - st.session_state.session_start
            st.info(f"⏱️ Session: {str(session_duration).split('.')[0]}")
        
        with col3:
            st.info(f"✅ Success: {st.session_state.success_count}")
        
        with col4:
            if st.session_state.error_count > 0:
                st.error(f"❌ Errors: {st.session_state.error_count}")
            else:
                st.success(f"❌ Errors: {st.session_state.error_count}")
    
    def render_sidebar(self):
        """Render the sidebar with settings and history."""
        with st.sidebar:
            st.header("⚙️ Settings")
            
            # User preferences
            st.session_state.user_preferences['show_sql'] = st.checkbox(
                "Show Generated SQL", 
                value=st.session_state.user_preferences['show_sql']
            )
            
            st.session_state.user_preferences['show_metadata'] = st.checkbox(
                "Show Query Metadata", 
                value=st.session_state.user_preferences['show_metadata']
            )
            
            st.session_state.user_preferences['default_format'] = st.selectbox(
                "Default Output Format",
                options=['table', 'json', 'csv', 'summary'],
                index=['table', 'json', 'csv', 'summary'].index(
                    st.session_state.user_preferences['default_format']
                )
            )
            
            st.session_state.user_preferences['max_rows_display'] = st.slider(
                "Max Rows to Display",
                min_value=10,
                max_value=200,
                value=st.session_state.user_preferences['max_rows_display'],
                step=10
            )
            
            st.markdown("---")
            
            # Pipeline status
            st.header("📊 Pipeline Status")
            if self.pipeline and st.session_state.pipeline_initialized:
                try:
                    status = self.pipeline.get_pipeline_status()
                    stats = status['pipeline_stats']
                    
                    st.metric("Total Queries", stats['total_queries'])
                    st.metric("Success Rate", f"{stats['successful_queries']}/{stats['total_queries']}")
                    
                    if stats['total_queries'] > 0:
                        success_rate = stats['successful_queries'] / stats['total_queries']
                        st.metric("Success %", f"{success_rate:.1%}")
                        st.metric("Avg Time", f"{stats['avg_total_time']:.2f}s")
                
                except Exception as e:
                    st.error(f"Error getting status: {e}")
            
            st.markdown("---")
            
            # Query history
            st.header("📝 Recent Queries")
            if st.session_state.query_history:
                for i, query in enumerate(reversed(st.session_state.query_history[-5:]), 1):
                    with st.expander(f"Query {len(st.session_state.query_history) - i + 1}"):
                        st.text(query['nlq'][:100] + "..." if len(query['nlq']) > 100 else query['nlq'])
                        st.caption(f"Status: {'✅' if query['success'] else '❌'} | Time: {query['timestamp'].strftime('%H:%M:%S')}")
            else:
                st.info("No queries yet")
            
            # Clear history button
            if st.button("🗑️ Clear History"):
                st.session_state.query_history = []
                st.rerun()
    
    def render_main_interface(self):
        """Render the main query interface."""
        # Initialize pipeline if needed
        if not self._initialize_pipeline():
            st.error("❌ Cannot proceed without pipeline initialization")
            return
        
        st.header("💬 Natural Language Query")
        
        # Query input
        query_input = st.text_area(
            "Enter your clinical question:",
            placeholder="e.g., How many patients do we have with diabetes?\nShow me all male patients over 65\nWhat are the most common diagnoses?",
            height=100,
            help="Ask questions about patients, diagnoses, medications, procedures, or any clinical data in natural language."
        )
        
        # Query options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            output_formats = st.multiselect(
                "Output Formats",
                options=['table', 'json', 'csv', 'summary'],
                default=[st.session_state.user_preferences['default_format']],
                help="Select one or more output formats for the results"
            )
        
        with col2:
            advanced_options = st.checkbox("Advanced Options", help="Show advanced query parameters")
        
        with col3:
            submit_button = st.button("🔍 Execute Query", type="primary", use_container_width=True)
        
        # Advanced options (if enabled)
        generation_params = {}
        execution_params = {}
        
        if advanced_options:
            with st.expander("🔧 Advanced Parameters"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("SQL Generation")
                    generation_params['num_beams'] = st.slider("Beam Search Width", 1, 10, 4)
                    generation_params['temperature'] = st.slider("Temperature", 0.1, 2.0, 1.0, 0.1)
                    generation_params['do_sample'] = st.checkbox("Enable Sampling", False)
                
                with col2:
                    st.subheader("Database Execution")
                    execution_params['timeout'] = st.slider("Query Timeout (s)", 10, 120, 30)
                    execution_params['max_rows'] = st.slider("Max Rows", 50, 1000, 200)
        
        # Process query
        if submit_button and query_input.strip():
            self._process_query(query_input.strip(), output_formats, generation_params, execution_params)
        elif submit_button:
            st.warning("⚠️ Please enter a query")
    
    def _process_query(self, nlq: str, output_formats: List[str], generation_params: Dict, execution_params: Dict):
        """Process a natural language query."""
        query_start_time = time.time()
        
        # Log query start
        self.activity_logger.log_activity(
            session_id=st.session_state.session_id,
            activity_type='query_start',
            details={'nlq': nlq, 'output_formats': output_formats},
            success=True
        )
        
        with st.spinner("🧠 Processing your query..."):
            try:
                # Process the query
                result = self.pipeline.process_query(
                    nlq=nlq,
                    output_formats=output_formats or ['table'],
                    user_id=st.session_state.session_id,
                    session_info={
                        'session_start': st.session_state.session_start.isoformat(),
                        'query_count': len(st.session_state.query_history) + 1
                    },
                    generation_params=generation_params,
                    execution_params=execution_params
                )
                
                query_time = time.time() - query_start_time
                
                # Add to history
                query_record = {
                    'nlq': nlq,
                    'success': result['success'],
                    'timestamp': datetime.now(),
                    'query_time': query_time,
                    'query_id': result.get('query_id', 'unknown')
                }
                st.session_state.query_history.append(query_record)
                
                if result['success']:
                    st.session_state.success_count += 1
                    self._display_successful_result(result)
                    
                    # Log successful query
                    self.activity_logger.log_activity(
                        session_id=st.session_state.session_id,
                        activity_type='query_success',
                        details={
                            'nlq': nlq,
                            'query_id': result['query_id'],
                            'rows_returned': result['metadata']['rows_returned'],
                            'total_time': result['metadata']['total_time']
                        },
                        success=True
                    )
                else:
                    st.session_state.error_count += 1
                    self._display_error_result(result)
                    
                    # Log failed query
                    self.activity_logger.log_activity(
                        session_id=st.session_state.session_id,
                        activity_type='query_error',
                        details={
                            'nlq': nlq,
                            'error': result['error'],
                            'error_type': result.get('error_type', 'unknown')
                        },
                        success=False
                    )
                    
                    # Handle error
                    self.error_handler.handle_error(
                        error=result['error'],
                        context={
                            'nlq': nlq,
                            'error_type': result.get('error_type', 'unknown'),
                            'pipeline_stage': result.get('pipeline_stage', 'unknown')
                        }
                    )
            
            except Exception as e:
                st.session_state.error_count += 1
                st.error(f"❌ Unexpected error: {e}")
                
                # Log exception
                self.activity_logger.log_activity(
                    session_id=st.session_state.session_id,
                    activity_type='query_exception',
                    details={'nlq': nlq, 'exception': str(e)},
                    success=False
                )
                
                self.error_handler.handle_error(
                    error=str(e),
                    context={'nlq': nlq, 'component': 'query_processing'}
                )
    
    def _display_successful_result(self, result: Dict[str, Any]):
        """Display successful query results."""
        st.success("✅ Query executed successfully!")
        
        # Show generated SQL if enabled
        if st.session_state.user_preferences['show_sql']:
            with st.expander("🔍 Generated SQL Query"):
                st.code(result['generated_sql'], language='sql')
        
        # Show metadata if enabled
        if st.session_state.user_preferences['show_metadata']:
            with st.expander("📊 Query Metadata"):
                metadata = result['metadata']
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Rows Returned", metadata['rows_returned'])
                with col2:
                    st.metric("Total Time", f"{metadata['total_time']:.3f}s")
                with col3:
                    st.metric("SQL Generation", f"{metadata['generation_time']:.3f}s")
                with col4:
                    st.metric("DB Execution", f"{metadata['execution_time']:.3f}s")
        
        # Display results in different formats
        formats = result['results']['formats']
        
        if len(formats) == 1:
            # Single format - display directly
            format_name = list(formats.keys())[0]
            self._display_format_result(format_name, formats[format_name])
        else:
            # Multiple formats - use tabs
            tab_names = list(formats.keys())
            tabs = st.tabs([f"📋 {name.upper()}" for name in tab_names])
            
            for tab, format_name in zip(tabs, tab_names):
                with tab:
                    self._display_format_result(format_name, formats[format_name])
    
    def _display_format_result(self, format_name: str, format_result: Dict[str, Any]):
        """Display results for a specific format."""
        if not format_result['success']:
            st.error(f"❌ {format_name.upper()} format failed: {format_result['error']}")
            return
        
        if format_name == 'table':
            self._display_table_result(format_result)
        elif format_name == 'json':
            self._display_json_result(format_result)
        elif format_name == 'csv':
            self._display_csv_result(format_result)
        elif format_name == 'summary':
            self._display_summary_result(format_result)
    
    def _display_table_result(self, format_result: Dict[str, Any]):
        """Display table format results."""
        data = format_result['data']
        
        if not data:
            st.info("📭 No data returned")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Limit rows for display
        max_rows = st.session_state.user_preferences['max_rows_display']
        if len(df) > max_rows:
            st.warning(f"⚠️ Showing first {max_rows} rows of {len(df)} total rows")
            display_df = df.head(max_rows)
        else:
            display_df = df
        
        # Display table
        st.dataframe(display_df, use_container_width=True)
        
        # Show basic statistics if numeric data
        numeric_cols = display_df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            with st.expander("📈 Basic Statistics"):
                st.dataframe(display_df[numeric_cols].describe())
        
        # Download button
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv_data,
            file_name=f"clinical_query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    def _display_json_result(self, format_result: Dict[str, Any]):
        """Display JSON format results."""
        json_data = format_result['data']
        
        # Pretty print JSON
        st.json(json_data)
        
        # Show size info
        size_mb = format_result.get('size_bytes', 0) / (1024 * 1024)
        st.caption(f"Size: {size_mb:.2f} MB")
        
        # Download button
        json_str = json.dumps(json_data, indent=2)
        st.download_button(
            label="📥 Download as JSON",
            data=json_str,
            file_name=f"clinical_query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    def _display_csv_result(self, format_result: Dict[str, Any]):
        """Display CSV format results."""
        csv_data = format_result['data']
        
        # Show CSV preview
        st.text_area("CSV Preview", csv_data[:1000] + "..." if len(csv_data) > 1000 else csv_data, height=200)
        
        # Download button
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=f"clinical_query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    def _display_summary_result(self, format_result: Dict[str, Any]):
        """Display summary format results."""
        summary = format_result['summary']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Data Overview")
            st.metric("Total Rows", summary.get('total_rows', 0))
            st.metric("Total Columns", summary.get('total_columns', 0))
            st.metric("Memory Usage", f"{summary.get('memory_usage_mb', 0):.2f} MB")
        
        with col2:
            st.subheader("🏷️ Data Types")
            data_types = summary.get('data_types', {})
            if data_types:
                for col_name, col_type in data_types.items():
                    st.text(f"{col_name}: {col_type}")
        
        # Column statistics if available
        if 'column_stats' in summary:
            st.subheader("📈 Column Statistics")
            stats_df = pd.DataFrame(summary['column_stats']).T
            st.dataframe(stats_df)
    
    def _display_error_result(self, result: Dict[str, Any]):
        """Display error results."""
        st.error(f"❌ Query failed: {result['error']}")
        
        # Show error details
        with st.expander("🔍 Error Details"):
            st.text(f"Error Type: {result.get('error_type', 'Unknown')}")
            st.text(f"Pipeline Stage: {result.get('pipeline_stage', 'Unknown')}")
            
            if 'generated_sql' in result:
                st.text("Generated SQL:")
                st.code(result['generated_sql'], language='sql')
        
        # Show suggestions
        error_type = result.get('error_type', '')
        if 'SQL_GENERATION' in error_type:
            st.info("💡 Try rephrasing your question or being more specific about what data you want.")
        elif 'DATABASE' in error_type:
            st.info("💡 The query might be too complex or reference non-existent data. Try a simpler question.")
        else:
            st.info("💡 Please try again or contact support if the problem persists.")
    
    def render_example_queries(self):
        """Render example queries section."""
        st.header("💡 Example Queries")
        
        examples = [
            {
                "category": "Patient Demographics",
                "queries": [
                    "How many patients do we have?",
                    "Show me all male patients over 65",
                    "What is the age distribution of our patients?",
                    "How many patients are from each city?"
                ]
            },
            {
                "category": "Medical Conditions",
                "queries": [
                    "Find patients with diabetes",
                    "What are the most common diagnoses?",
                    "Show patients with multiple chronic conditions",
                    "How many patients have hypertension?"
                ]
            },
            {
                "category": "Healthcare Providers",
                "queries": [
                    "List all healthcare organizations",
                    "Which provider sees the most patients?",
                    "Show me all cardiologists",
                    "What specialties do we have?"
                ]
            },
            {
                "category": "Medications",
                "queries": [
                    "What medications are most commonly prescribed?",
                    "Show patients taking insulin",
                    "Find all diabetes medications",
                    "Which patients are on multiple medications?"
                ]
            }
        ]
        
        for example in examples:
            with st.expander(f"📂 {example['category']}"):
                for query in example['queries']:
                    if st.button(f"▶️ {query}", key=f"example_{query}"):
                        # Set the query in the text area (this would require some state management)
                        st.session_state.example_query = query
                        st.rerun()
    
    def run(self):
        """Run the Streamlit application."""
        try:
            # Render components
            self.render_header()
            self.render_sidebar()
            
            # Main content
            tab1, tab2, tab3, tab4 = st.tabs(["🔍 Query Interface", "🗄️ Database Explorer", "💡 Examples", "📊 Analytics"])
            
            with tab1:
                self.render_main_interface()
            
            with tab2:
                self.database_explorer.render_full_explorer()
            
            with tab3:
                self.render_example_queries()
            
            with tab4:
                self.render_analytics()
            
        except Exception as e:
            st.error(f"❌ Application error: {e}")
            self.error_handler.handle_error(
                error=str(e),
                context={'component': 'main_app'}
            )
        finally:
            # Cleanup database connections
            if hasattr(self, 'database_explorer'):
                self.database_explorer.cleanup()
    
    def render_analytics(self):
        """Render analytics and monitoring dashboard."""
        st.header("📊 Session Analytics")
        
        if not st.session_state.query_history:
            st.info("📭 No queries executed yet")
            return
        
        # Create analytics DataFrame
        df = pd.DataFrame(st.session_state.query_history)
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Queries", len(df))
        
        with col2:
            success_rate = df['success'].mean()
            st.metric("Success Rate", f"{success_rate:.1%}")
        
        with col3:
            avg_time = df['query_time'].mean()
            st.metric("Avg Query Time", f"{avg_time:.2f}s")
        
        with col4:
            session_duration = datetime.now() - st.session_state.session_start
            st.metric("Session Duration", str(session_duration).split('.')[0])
        
        # Query timeline
        st.subheader("📈 Query Timeline")
        df['timestamp_str'] = df['timestamp'].dt.strftime('%H:%M:%S')
        
        fig = px.scatter(
            df, 
            x='timestamp', 
            y='query_time',
            color='success',
            hover_data=['nlq'],
            title="Query Performance Over Time"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Success/failure breakdown
        st.subheader("✅ Success/Failure Breakdown")
        success_counts = df['success'].value_counts()
        
        fig = px.pie(
            values=success_counts.values,
            names=['Success' if x else 'Failed' for x in success_counts.index],
            title="Query Success Rate"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Recent queries table
        st.subheader("📝 Recent Queries")
        display_df = df[['timestamp', 'nlq', 'success', 'query_time']].copy()
        display_df['timestamp'] = display_df['timestamp'].dt.strftime('%H:%M:%S')
        display_df['nlq'] = display_df['nlq'].str[:100] + '...'
        display_df['success'] = display_df['success'].map({True: '✅', False: '❌'})
        display_df['query_time'] = display_df['query_time'].round(3)
        
        st.dataframe(display_df, use_container_width=True)

def main():
    """Main function to run the Streamlit app."""
    app = ClinicalNLQApp()
    app.run()

if __name__ == "__main__":
    main()