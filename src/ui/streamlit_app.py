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
from nlq.rag_inference_engine import RAGEnhancedInferenceEngine
from ui.session_manager import SessionManager
from ui.activity_logger import ActivityLogger
from ui.ui_components import UIComponents
from ui.error_handler import UIErrorHandler
from ui.database_explorer import DatabaseExplorer

# Page configuration
st.set_page_config(
    page_title="RAG-Enhanced Clinical NLQ Assistant",
    page_icon="🏥🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/clinical-nlq',
        'Report a bug': 'https://github.com/your-repo/clinical-nlq/issues',
        'About': "RAG-Enhanced Clinical Natural Language Query Assistant - Advanced AI-powered query processing with retrieval-augmented generation."
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
                'max_rows_display': 50,
                'use_rag': True  # Enable RAG by default
            }
            st.session_state.error_count = 0
            st.session_state.success_count = 0
            st.session_state.rag_engine = None
            st.session_state.rag_initialized = False
    
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
    
    @st.cache_resource
    def _get_rag_engine(_self):
        """Get or create the RAG-enhanced inference engine (cached)."""
        try:
            rag_engine = RAGEnhancedInferenceEngine()
            return rag_engine
        except Exception as e:
            st.error(f"Failed to create RAG engine: {e}")
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
    
    def _initialize_rag_engine(self):
        """Initialize the RAG engine if not already done."""
        if not st.session_state.rag_initialized and st.session_state.user_preferences.get('use_rag', False):
            with st.spinner("🤖 Initializing RAG-Enhanced Engine..."):
                try:
                    rag_engine = self._get_rag_engine()
                    if rag_engine:
                        # Load model
                        if rag_engine.load_model():
                            # Initialize RAG system
                            if rag_engine.initialize_rag_system():
                                st.session_state.rag_engine = rag_engine
                                st.session_state.rag_initialized = True
                                st.success("✅ RAG system initialized successfully!")
                                return True
                            else:
                                st.warning("⚠️ RAG system initialization failed, using traditional approach")
                        else:
                            st.warning("⚠️ Model loading failed, using traditional approach")
                except Exception as e:
                    st.warning(f"⚠️ RAG initialization error: {e}")
                    return False
        
        return st.session_state.rag_initialized
    
    def render_header(self):
        """Render the application header."""
        st.title("🏥🤖 RAG-Enhanced Clinical NLQ Assistant")
        st.markdown("*Advanced AI-powered natural language query processing with retrieval-augmented generation*")
        st.markdown("---")
        
        # Status indicators
        col1, col2, col3, col4, col5 = st.columns(5)
        
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
        
        with col5:
            if st.session_state.rag_initialized:
                st.success("🤖 RAG Ready")
            elif st.session_state.user_preferences.get('use_rag', True):
                st.warning("🤖 RAG Loading")
            else:
                st.info("🤖 RAG Disabled")
    
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
            
            # RAG Settings
            st.markdown("### 🤖 RAG Enhancement")
            
            use_rag = st.checkbox(
                "Enable RAG Enhancement",
                value=st.session_state.user_preferences.get('use_rag', True),
                help="Use Retrieval-Augmented Generation for better query processing"
            )
            st.session_state.user_preferences['use_rag'] = use_rag
            
            # LLM Selection
            if use_rag:
                llm_options = ["gemini", "openai", "none"]
                preferred_llm = st.selectbox(
                    "🧠 Preferred LLM",
                    options=llm_options,
                    index=llm_options.index(st.session_state.user_preferences.get('preferred_llm', 'gemini')),
                    help="Choose which LLM to use for query enhancement"
                )
                st.session_state.user_preferences['preferred_llm'] = preferred_llm
                
                # SQL Generation Method
                sql_method = st.radio(
                    "🔧 SQL Generation Method",
                    options=["T5 Model (Enhanced)", "Gemini Direct", "Hybrid"],
                    index=0,
                    help="Choose how to generate SQL queries"
                )
                st.session_state.user_preferences['sql_method'] = sql_method
            
            # Initialize RAG if enabled
            if use_rag and not st.session_state.rag_initialized:
                if st.button("🚀 Initialize RAG System"):
                    self._initialize_rag_engine()
            
            # RAG Status
            if st.session_state.rag_initialized:
                st.success("✅ RAG System Ready")
                if st.session_state.rag_engine:
                    stats = st.session_state.rag_engine.get_comprehensive_stats()
                    gen_stats = stats.get('generation_stats', {})
                    if gen_stats.get('total_queries', 0) > 0:
                        st.metric("RAG Success Rate", f"{gen_stats.get('rag_enhancement_rate', 0)*100:.1f}%")
            elif use_rag:
                st.warning("⚠️ RAG System Not Initialized")
            else:
                st.info("ℹ️ RAG Enhancement Disabled")
            
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
        
        # Helpful tips
        with st.expander("💡 Query Examples & Tips"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**✅ Good Natural Language Examples:**")
                st.markdown("""
                - How many patients do we have?
                - Show me all male patients
                - Find patients with diabetes
                - What medications are most prescribed?
                - List patients over 65 years old
                - Which provider sees the most patients?
                """)
            
            with col2:
                st.markdown("**❌ Don't Enter SQL Code:**")
                st.markdown("""
                - ~~SELECT COUNT(*) FROM patients~~
                - ~~SELECT * FROM conditions WHERE...~~
                - ~~INSERT INTO table...~~
                
                **Instead, ask in plain English!**
                The AI will convert your question to SQL automatically.
                """)
        
        # Quick example buttons
        st.markdown("**🚀 Quick Examples:**")
        example_col1, example_col2, example_col3 = st.columns(3)
        
        with example_col1:
            if st.button("👥 Patient Count"):
                st.session_state.example_query = "How many patients do we have?"
        
        with example_col2:
            if st.button("🏥 Common Conditions"):
                st.session_state.example_query = "What are the most common medical conditions?"
        
        with example_col3:
            if st.button("💊 Medications"):
                st.session_state.example_query = "Show me the most frequently prescribed medications"
        
        # Use example query if selected
        if hasattr(st.session_state, 'example_query') and st.session_state.example_query:
            query_input = st.session_state.example_query
            st.session_state.example_query = None  # Clear after use
        
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
    
    def _is_sql_query(self, text: str) -> bool:
        """
        Detect if the input text is SQL rather than natural language.
        
        Args:
            text: Input text to check
            
        Returns:
            True if text appears to be SQL, False otherwise
        """
        text_upper = text.upper().strip()
        
        # Common SQL keywords that indicate SQL rather than natural language
        sql_indicators = [
            'SELECT ',
            'INSERT ',
            'UPDATE ',
            'DELETE ',
            'CREATE ',
            'DROP ',
            'ALTER ',
            'TRUNCATE ',
            'WITH '
        ]
        
        # Check if text starts with SQL keywords
        for indicator in sql_indicators:
            if text_upper.startswith(indicator):
                return True
        
        # Additional checks for SQL patterns
        if ('FROM ' in text_upper and 
            ('SELECT' in text_upper or 'COUNT(' in text_upper or 'SUM(' in text_upper)):
            return True
        
        # Check for common SQL patterns
        sql_patterns = [
            'COUNT(*)',
            'COUNT(1)',
            'GROUP BY',
            'ORDER BY',
            'WHERE ',
            'HAVING ',
            'INNER JOIN',
            'LEFT JOIN',
            'RIGHT JOIN'
        ]
        
        for pattern in sql_patterns:
            if pattern in text_upper:
                return True
        
        return False
    
    def _execute_sql_directly(self, sql: str, output_formats: List[str], execution_params: Dict):
        """
        Execute SQL directly without NLQ processing.
        
        Args:
            sql: SQL query to execute
            output_formats: Requested output formats
            execution_params: Execution parameters
        """
        try:
            from nlq.database_executor import DatabaseExecutor
            
            with st.spinner("🗄️ Executing SQL query..."):
                db_executor = DatabaseExecutor()
                # Connect to database first
                if not db_executor.connect():
                    st.error("❌ **Database Connection Failed**: Unable to connect to the database.")
                    return
                
                exec_result = db_executor.execute_query(sql, **execution_params)
                
                if exec_result['success']:
                    st.success("✅ **SQL executed successfully!**")
                    
                    # Display results
                    if exec_result['data'] is not None and not exec_result['data'].empty:
                        st.subheader("📊 Query Results")
                        st.dataframe(exec_result['data'], use_container_width=True)
                        
                        # Show execution stats
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Rows Returned", len(exec_result['data']))
                        with col2:
                            st.metric("Execution Time", f"{exec_result['execution_time']:.3f}s")
                        with col3:
                            st.metric("Columns", len(exec_result['data'].columns))
                        
                        # Export options
                        if 'CSV' in output_formats:
                            csv = exec_result['data'].to_csv(index=False)
                            st.download_button(
                                label="📥 Download CSV",
                                data=csv,
                                file_name=f"sql_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                    else:
                        st.info("✅ Query executed successfully (no data returned)")
                else:
                    st.error(f"❌ **SQL execution failed**: {exec_result.get('error', 'Unknown error')}")
                    
        except Exception as e:
            st.error(f"❌ **Error executing SQL**: {str(e)}")
            
        # Log the direct SQL execution
        self.activity_logger.log_activity(
            session_id=st.session_state.session_id,
            activity_type='direct_sql_execution',
            details={'sql': sql, 'output_formats': output_formats},
            success=exec_result.get('success', False) if 'exec_result' in locals() else False
        )
    
    def _process_query(self, nlq: str, output_formats: List[str], generation_params: Dict, execution_params: Dict):
        """Process a natural language query."""
        query_start_time = time.time()
        
        # Check if input is already SQL
        if self._is_sql_query(nlq):
            st.warning("⚠️ **SQL Detected**: You entered SQL code instead of a natural language question.")
            st.info("💡 **Try instead**: Ask in plain English like 'How many patients do we have?' or 'Show me all male patients'")
            
            # Show the SQL they entered for reference
            st.code(nlq, language='sql')
            
            # Offer to execute it directly
            if st.button("🚀 Execute this SQL directly"):
                self._execute_sql_directly(nlq, output_formats, execution_params)
            return
        
        # Log query start
        self.activity_logger.log_activity(
            session_id=st.session_state.session_id,
            activity_type='query_start',
            details={'nlq': nlq, 'output_formats': output_formats},
            success=True
        )
        
        with st.spinner("🧠 Processing your query..."):
            try:
                # Use RAG engine if available and enabled
                if st.session_state.rag_initialized and st.session_state.user_preferences.get('use_rag', False):
                    # Get SQL generation method preference
                    sql_method = st.session_state.user_preferences.get('sql_method', 'T5 Model (Enhanced)')
                    
                    if sql_method == 'Gemini Direct':
                        # Use Gemini directly for SQL generation
                        rag_result = st.session_state.rag_engine.generate_sql_with_gemini(
                            nlq, 
                            use_rag=True
                        )
                    elif sql_method == 'Hybrid':
                        # Try Gemini first, fallback to T5
                        try:
                            rag_result = st.session_state.rag_engine.generate_sql_with_gemini(
                                nlq, 
                                use_rag=True
                            )
                            if not rag_result['validation']['is_valid']:
                                # Fallback to T5
                                rag_result = st.session_state.rag_engine.generate_sql(
                                    nlq, 
                                    use_rag=True,
                                    **generation_params
                                )
                                rag_result['metadata']['method'] = 'hybrid_t5_fallback'
                        except Exception:
                            # Fallback to T5 on error
                            rag_result = st.session_state.rag_engine.generate_sql(
                                nlq, 
                                use_rag=True,
                                **generation_params
                            )
                            rag_result['metadata']['method'] = 'hybrid_t5_fallback'
                    else:
                        # Default: T5 Model (Enhanced)
                        rag_result = st.session_state.rag_engine.generate_sql(
                            nlq, 
                            use_rag=True,
                            **generation_params
                        )
                    
                    # Convert RAG result to pipeline format
                    result = {
                        'success': rag_result['validation']['is_valid'],
                        'generated_sql': rag_result['generated_sql'],
                        'nlq': rag_result['nlq'],
                        'metadata': rag_result['metadata'],
                        'validation': rag_result['validation'],
                        'generation_time': rag_result['generation_time'],
                        'rag_enhanced': True
                    }
                    
                    # Execute SQL if valid and execution is requested
                    if result['success'] and 'table' in output_formats:
                        try:
                            from nlq.database_executor import DatabaseExecutor
                            db_executor = DatabaseExecutor()
                            # Connect to database first
                            if db_executor.connect():
                                exec_result = db_executor.execute_query(result['generated_sql'])
                                result['execution'] = exec_result
                                
                                # Add debug info for successful execution
                                if exec_result.get('success'):
                                    data = exec_result.get('data', [])
                                    logger.info(f"✅ RAG query executed successfully: {len(data) if data else 0} rows returned")
                                else:
                                    logger.warning(f"⚠️ RAG query execution failed: {exec_result.get('error', 'Unknown error')}")
                            else:
                                error_msg = 'Failed to connect to database - check PostgreSQL service and credentials'
                                logger.error(f"❌ Database connection failed for RAG query")
                                result['execution'] = {'success': False, 'error': error_msg}
                        except ImportError as e:
                            error_msg = f'Failed to import DatabaseExecutor: {str(e)}'
                            logger.error(f"❌ Import error: {error_msg}")
                            result['execution'] = {'success': False, 'error': error_msg}
                        except Exception as e:
                            error_msg = f'Database execution error: {str(e)}'
                            logger.error(f"❌ Unexpected error during RAG query execution: {error_msg}")
                            result['execution'] = {'success': False, 'error': error_msg}
                else:
                    # Use traditional pipeline
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
                    result['rag_enhanced'] = False
                
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
                            'query_id': result.get('query_id', 'unknown'),
                            'rows_returned': result.get('metadata', {}).get('rows_returned', 0),
                            'total_time': result.get('metadata', {}).get('total_time', query_time)
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
                
                # More descriptive error message
                error_msg = str(e)
                if error_msg == "'results'":
                    st.error("❌ **Result Display Error**: There was an issue displaying the query results. This might be due to a mismatch in result format.")
                    st.info("💡 **Suggestion**: Try refreshing the page and running your query again. If the issue persists, try using a simpler query format.")
                elif error_msg == "'query_id'":
                    st.error("❌ **Query ID Error**: There was an issue with query tracking. This is a system error that doesn't affect query functionality.")
                    st.info("💡 **Suggestion**: Your query may have processed correctly. Check the results below or try running the query again.")
                else:
                    st.error(f"❌ **Unexpected Error**: {error_msg}")
                
                # Log exception with more context
                self.activity_logger.log_activity(
                    session_id=st.session_state.session_id,
                    activity_type='query_exception',
                    details={
                        'nlq': nlq, 
                        'exception': error_msg,
                        'error_type': type(e).__name__,
                        'traceback': str(e.__class__.__name__)
                    },
                    success=False
                )
                
                self.error_handler.handle_error(
                    error=error_msg,
                    context={
                        'nlq': nlq, 
                        'component': 'query_processing',
                        'error_type': type(e).__name__
                    }
                )
    
    def _display_successful_result(self, result: Dict[str, Any]):
        """Display successful query results."""
        # Success message with RAG indicator
        if result.get('rag_enhanced', False):
            st.success("✅ Query executed successfully with RAG enhancement!")
        else:
            st.success("✅ Query executed successfully!")
        
        # RAG Enhancement Information
        if result.get('rag_enhanced', False) and result.get('metadata', {}).get('rag_info'):
            with st.expander("🤖 RAG Enhancement Details"):
                rag_info = result['metadata']['rag_info']
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Enhancement Method", rag_info.get('method_used', 'unknown').replace('_', ' ').title())
                with col2:
                    st.metric("Confidence Score", f"{rag_info.get('confidence_score', 0):.3f}")
                with col3:
                    st.metric("RAG Processing Time", f"{rag_info.get('processing_time', 0):.3f}s")
                
                # Show similar examples if available
                if rag_info.get('similar_examples'):
                    st.markdown("**Similar Training Examples Used:**")
                    for i, example in enumerate(rag_info['similar_examples'][:3], 1):
                        st.text(f"{i}. \"{example['extracted_nlq']}\" (similarity: {example['similarity_score']:.3f})")
        
        # Show generated SQL if enabled
        if st.session_state.user_preferences['show_sql']:
            with st.expander("🔍 Generated SQL Query"):
                st.code(result['generated_sql'], language='sql')
        
        # Show metadata if enabled
        if st.session_state.user_preferences['show_metadata']:
            with st.expander("📊 Query Metadata"):
                metadata = result.get('metadata', {})
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    # Handle different metadata structures
                    rows_returned = metadata.get('rows_returned', 0)
                    if 'execution' in result and result['execution'].get('data') is not None:
                        rows_returned = len(result['execution']['data'])
                    st.metric("Rows Returned", rows_returned)
                with col2:
                    total_time = metadata.get('total_time', result.get('generation_time', 0))
                    st.metric("Total Time", f"{total_time:.3f}s")
                with col3:
                    generation_time = metadata.get('generation_time', result.get('generation_time', 0))
                    st.metric("SQL Generation", f"{generation_time:.3f}s")
                with col4:
                    exec_time = metadata.get('execution_time', 0)
                    if 'execution' in result:
                        exec_time = result['execution'].get('execution_time', 0)
                    st.metric("DB Execution", f"{exec_time:.3f}s")
        
        # Display results in different formats
        # Handle different result structures (RAG vs traditional pipeline)
        if 'results' in result and 'formats' in result['results']:
            # Traditional pipeline result structure
            formats = result['results']['formats']
        elif 'execution' in result:
            # RAG result structure with execution data
            if result['execution'].get('success'):
                formats = {'table': result['execution']}
            else:
                # Execution failed - show error
                st.error(f"❌ **Query execution failed**: {result['execution'].get('error', 'Unknown database error')}")
                st.info("💡 **Generated SQL was valid, but database execution failed. Check database connection.**")
                if st.session_state.user_preferences['show_sql']:
                    with st.expander("🔍 Generated SQL Query"):
                        st.code(result['generated_sql'], language='sql')
                return
        else:
            # No execution results to display
            st.info("📋 SQL generated successfully. Enable table output to see query results.")
            return
        
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
        # Handle different data structures
        if 'data' in format_result:
            # Traditional pipeline format
            data = format_result['data']
            if data is None or (isinstance(data, list) and len(data) == 0):
                st.info("📭 No data returned")
                return
            # Convert to DataFrame if it's not already
            if isinstance(data, pd.DataFrame):
                df = data
            else:
                df = pd.DataFrame(data)
        else:
            # RAG execution result format - format_result is the execution result itself
            if not format_result.get('success', False):
                st.error(f"❌ Query execution failed: {format_result.get('error', 'Unknown error')}")
                return
            
            data = format_result.get('data')
            if data is None or (hasattr(data, 'empty') and data.empty):
                st.info("📭 No data returned")
                return
            
            df = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
        
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
            # Initialize systems
            self._initialize_pipeline()
            if st.session_state.user_preferences.get('use_rag', True):
                self._initialize_rag_engine()
            
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