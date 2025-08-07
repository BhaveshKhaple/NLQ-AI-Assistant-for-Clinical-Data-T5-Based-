#!/usr/bin/env python3
"""
RAG-Enhanced Clinical NLQ Streamlit Web Interface
Enhanced Streamlit application with RAG-powered query processing.
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

from nlq.rag_inference_engine import RAGEnhancedInferenceEngine
from nlq.database_executor import DatabaseExecutor
from nlq.result_formatter import ResultFormatter
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

class RAGEnhancedClinicalNLQApp:
    """RAG-Enhanced Streamlit application class."""
    
    def __init__(self):
        """Initialize the RAG-enhanced application."""
        self.session_manager = SessionManager()
        self.activity_logger = ActivityLogger()
        self.ui_components = UIComponents()
        self.error_handler = UIErrorHandler()
        self.database_explorer = DatabaseExplorer()
        
        # Initialize RAG-enhanced inference engine
        self.inference_engine = None
        self.database_executor = None
        self.result_formatter = None
        
        # Initialize session state
        self._initialize_session_state()
        
        # Load components
        self._load_components()
    
    def _initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        if 'session_id' not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
        
        if 'query_history' not in st.session_state:
            st.session_state.query_history = []
        
        if 'rag_enabled' not in st.session_state:
            st.session_state.rag_enabled = True
        
        if 'rag_stats' not in st.session_state:
            st.session_state.rag_stats = {}
        
        if 'model_loaded' not in st.session_state:
            st.session_state.model_loaded = False
        
        if 'rag_initialized' not in st.session_state:
            st.session_state.rag_initialized = False
    
    @st.cache_resource
    def _load_components(_self):
        """Load and cache the inference components."""
        try:
            # Initialize RAG-enhanced inference engine
            inference_engine = RAGEnhancedInferenceEngine()
            
            # Load model
            if inference_engine.load_model():
                st.session_state.model_loaded = True
                
                # Initialize RAG system
                if inference_engine.initialize_rag_system():
                    st.session_state.rag_initialized = True
            
            # Initialize other components
            database_executor = DatabaseExecutor()
            result_formatter = ResultFormatter()
            
            return inference_engine, database_executor, result_formatter
            
        except Exception as e:
            st.error(f"❌ Error loading components: {e}")
            return None, None, None
    
    def _load_components(self):
        """Load components using cached function."""
        self.inference_engine, self.database_executor, self.result_formatter = self._load_components()
    
    def render_header(self):
        """Render the application header."""
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h1>🏥🤖 RAG-Enhanced Clinical NLQ Assistant</h1>
            <p style="font-size: 1.2em; color: #666;">
                Advanced AI-powered natural language query processing with retrieval-augmented generation
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_sidebar(self):
        """Render the sidebar with controls and information."""
        with st.sidebar:
            st.markdown("## ⚙️ Settings")
            
            # RAG Settings
            st.markdown("### 🔍 RAG Enhancement")
            rag_enabled = st.checkbox(
                "Enable RAG Enhancement",
                value=st.session_state.rag_enabled,
                help="Use retrieval-augmented generation to improve query processing"
            )
            st.session_state.rag_enabled = rag_enabled
            
            if st.session_state.rag_initialized:
                st.success("✅ RAG System Ready")
                st.info(f"📚 Training Examples: 4,588")
            else:
                st.warning("⚠️ RAG System Not Available")
            
            # Model Settings
            st.markdown("### 🤖 Model Settings")
            if st.session_state.model_loaded:
                st.success("✅ T5 Model Loaded")
                
                # Generation parameters
                with st.expander("Generation Parameters"):
                    num_beams = st.slider("Number of Beams", 1, 8, 4)
                    max_length = st.slider("Max Length", 50, 512, 256)
                    temperature = st.slider("Temperature", 0.1, 2.0, 1.0, 0.1)
                    do_sample = st.checkbox("Use Sampling", False)
                    
                    st.session_state.generation_params = {
                        'num_beams': num_beams,
                        'max_length': max_length,
                        'temperature': temperature,
                        'do_sample': do_sample
                    }
            else:
                st.error("❌ Model Not Loaded")
            
            # Statistics
            st.markdown("### 📊 Session Statistics")
            if st.session_state.rag_stats:
                stats = st.session_state.rag_stats
                st.metric("Total Queries", stats.get('total_queries', 0))
                st.metric("RAG Enhanced", f"{stats.get('rag_enhancement_rate', 0)*100:.1f}%")
                st.metric("Success Rate", f"{stats.get('success_rate', 0)*100:.1f}%")
                st.metric("Avg Time", f"{stats.get('avg_time', 0):.2f}s")
            
            # Query History
            st.markdown("### 📝 Recent Queries")
            if st.session_state.query_history:
                for i, query in enumerate(reversed(st.session_state.query_history[-5:]), 1):
                    with st.expander(f"Query {i}"):
                        st.text(query['nlq'][:50] + "..." if len(query['nlq']) > 50 else query['nlq'])
                        st.text(f"Method: {query.get('method', 'unknown')}")
                        st.text(f"Valid: {'✅' if query.get('valid', False) else '❌'}")
            else:
                st.info("No queries yet")
    
    def render_main_interface(self):
        """Render the main query interface."""
        if not st.session_state.model_loaded:
            st.error("❌ Model not loaded. Please check the system configuration.")
            return
        
        # Query input section
        st.markdown("## 💬 Ask Your Clinical Question")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            user_query = st.text_input(
                "Enter your natural language query:",
                placeholder="e.g., How many patients with diabetes do we have?",
                help="Ask questions about patients, conditions, medications, providers, etc."
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
            process_query = st.button("🔍 Process Query", type="primary")
        
        # Example queries
        st.markdown("### 💡 Example Queries")
        example_queries = [
            "How many patients do we have?",
            "Show me all diabetic patients",
            "List medications for hypertension",
            "Find high-cost patients",
            "What are the most common conditions?",
            "Show patients with multiple chronic conditions"
        ]
        
        cols = st.columns(3)
        for i, example in enumerate(example_queries):
            with cols[i % 3]:
                if st.button(example, key=f"example_{i}"):
                    user_query = example
                    process_query = True
        
        # Process query
        if process_query and user_query:
            self.process_query(user_query)
        elif process_query and not user_query:
            st.warning("⚠️ Please enter a query first.")
    
    def process_query(self, user_query: str):
        """Process a user query with RAG enhancement."""
        if not self.inference_engine:
            st.error("❌ Inference engine not available")
            return
        
        with st.spinner("🔄 Processing your query..."):
            start_time = time.time()
            
            try:
                # Generate SQL with RAG enhancement
                generation_params = getattr(st.session_state, 'generation_params', {})
                result = self.inference_engine.generate_sql(
                    user_query,
                    use_rag=st.session_state.rag_enabled,
                    **generation_params
                )
                
                processing_time = time.time() - start_time
                
                # Display results
                self.display_results(user_query, result, processing_time)
                
                # Update statistics
                self.update_statistics(result)
                
                # Log activity
                self.activity_logger.log_query(
                    session_id=st.session_state.session_id,
                    query=user_query,
                    result=result,
                    processing_time=processing_time
                )
                
            except Exception as e:
                st.error(f"❌ Error processing query: {e}")
                self.error_handler.handle_error(e, {"query": user_query})
    
    def display_results(self, user_query: str, result: Dict[str, Any], processing_time: float):
        """Display query results with enhanced information."""
        st.markdown("## 📊 Query Results")
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["🎯 Results", "🔍 RAG Info", "⚙️ Technical", "📈 Execution"])
        
        with tab1:
            self.display_main_results(user_query, result, processing_time)
        
        with tab2:
            self.display_rag_information(result)
        
        with tab3:
            self.display_technical_details(result)
        
        with tab4:
            self.display_execution_results(user_query, result)
    
    def display_main_results(self, user_query: str, result: Dict[str, Any], processing_time: float):
        """Display main query results."""
        # Query information
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Processing Time", f"{processing_time:.2f}s")
        
        with col2:
            st.metric("SQL Valid", "✅" if result['validation']['is_valid'] else "❌")
        
        with col3:
            method = result['metadata'].get('method', 'unknown')
            st.metric("Method", method.replace('_', ' ').title())
        
        with col4:
            rag_enhanced = result['metadata'].get('rag_enhanced', False)
            st.metric("RAG Enhanced", "✅" if rag_enhanced else "❌")
        
        # Generated SQL
        st.markdown("### 🔧 Generated SQL")
        if result['validation']['is_valid']:
            st.code(result['generated_sql'], language='sql')
        else:
            st.error("❌ Invalid SQL Generated")
            st.code(result['generated_sql'], language='sql')
            
            if result['validation'].get('errors'):
                st.markdown("**Errors:**")
                for error in result['validation']['errors']:
                    st.error(f"• {error}")
        
        # Warnings
        if result['validation'].get('warnings'):
            st.markdown("**Warnings:**")
            for warning in result['validation']['warnings']:
                st.warning(f"• {warning}")
    
    def display_rag_information(self, result: Dict[str, Any]):
        """Display RAG-specific information."""
        rag_info = result['metadata'].get('rag_info')
        
        if not rag_info:
            st.info("ℹ️ RAG enhancement was not used for this query.")
            return
        
        st.markdown("### 🔍 RAG Enhancement Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Enhancement Method", rag_info['method_used'].replace('_', ' ').title())
            st.metric("Confidence Score", f"{rag_info['confidence_score']:.3f}")
            st.metric("Processing Time", f"{rag_info['processing_time']:.3f}s")
        
        with col2:
            if rag_info['enhanced_query'] != rag_info['original_query']:
                st.markdown("**Query Enhancement:**")
                st.text_area("Original", rag_info['original_query'], height=60, disabled=True)
                st.text_area("Enhanced", rag_info['enhanced_query'], height=60, disabled=True)
        
        # Similar examples
        if rag_info.get('similar_examples'):
            st.markdown("### 📚 Similar Training Examples")
            
            for i, example in enumerate(rag_info['similar_examples'][:3], 1):
                with st.expander(f"Example {i} (Similarity: {example['similarity_score']:.3f})"):
                    st.markdown("**Query:**")
                    st.text(example['extracted_nlq'])
                    st.markdown("**SQL:**")
                    st.code(example['target_text'], language='sql')
    
    def display_technical_details(self, result: Dict[str, Any]):
        """Display technical details about the generation process."""
        st.markdown("### ⚙️ Technical Details")
        
        metadata = result['metadata']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Generation Info:**")
            st.json({
                'method': metadata.get('method', 'unknown'),
                'input_length': metadata.get('input_length', 0),
                'output_length': metadata.get('output_length', 0),
                'tokens_generated': metadata.get('tokens_generated', 0)
            })
        
        with col2:
            st.markdown("**Validation Results:**")
            validation = result['validation']
            st.json({
                'is_valid': validation['is_valid'],
                'has_select': validation.get('has_select', False),
                'has_from': validation.get('has_from', False),
                'has_schema_prefix': validation.get('has_schema_prefix', False),
                'sql_length': validation.get('sql_length', 0)
            })
        
        # Generation config
        if 'generation_config' in result:
            st.markdown("**Generation Configuration:**")
            st.json(result['generation_config'])
    
    def display_execution_results(self, user_query: str, result: Dict[str, Any]):
        """Display database execution results."""
        if not result['validation']['is_valid']:
            st.warning("⚠️ Cannot execute invalid SQL")
            return
        
        if not self.database_executor:
            st.warning("⚠️ Database executor not available")
            return
        
        st.markdown("### 📈 Database Execution")
        
        execute_query = st.button("🚀 Execute Query", type="secondary")
        
        if execute_query:
            with st.spinner("🔄 Executing query..."):
                try:
                    execution_result = self.database_executor.execute_query(result['generated_sql'])
                    
                    if execution_result['success']:
                        st.success(f"✅ Query executed successfully in {execution_result['execution_time']:.3f}s")
                        
                        if execution_result['data']:
                            df = pd.DataFrame(execution_result['data'])
                            st.dataframe(df, use_container_width=True)
                            
                            # Download option
                            csv = df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download CSV",
                                data=csv,
                                file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                        else:
                            st.info("ℹ️ Query executed but returned no data")
                    else:
                        st.error(f"❌ Query execution failed: {execution_result['error']}")
                        
                except Exception as e:
                    st.error(f"❌ Error executing query: {e}")
    
    def update_statistics(self, result: Dict[str, Any]):
        """Update session statistics."""
        # Add to query history
        query_info = {
            'nlq': result['nlq'],
            'method': result['metadata'].get('method', 'unknown'),
            'valid': result['validation']['is_valid'],
            'rag_enhanced': result['metadata'].get('rag_enhanced', False),
            'timestamp': datetime.now().isoformat()
        }
        st.session_state.query_history.append(query_info)
        
        # Update RAG statistics
        if self.inference_engine:
            stats = self.inference_engine.get_comprehensive_stats()
            gen_stats = stats.get('generation_stats', {})
            
            if gen_stats.get('total_queries', 0) > 0:
                st.session_state.rag_stats = {
                    'total_queries': gen_stats['total_queries'],
                    'rag_enhancement_rate': gen_stats.get('rag_enhancement_rate', 0),
                    'success_rate': gen_stats['successful_generations'] / gen_stats['total_queries'],
                    'avg_time': gen_stats.get('avg_time', 0)
                }
    
    def render_rag_dashboard(self):
        """Render RAG system dashboard."""
        st.markdown("## 🤖 RAG System Dashboard")
        
        if not st.session_state.rag_initialized:
            st.warning("⚠️ RAG system not initialized")
            return
        
        if not self.inference_engine:
            st.error("❌ Inference engine not available")
            return
        
        # Get comprehensive stats
        stats = self.inference_engine.get_comprehensive_stats()
        
        # Model information
        st.markdown("### 🔧 Model Information")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Parameters", f"{stats.get('total_parameters', 0):,}")
        
        with col2:
            st.metric("Model Size", f"{stats.get('model_size_mb', 0):.1f} MB")
        
        with col3:
            st.metric("Device", stats.get('device', 'unknown'))
        
        # Generation statistics
        gen_stats = stats.get('generation_stats', {})
        if gen_stats.get('total_queries', 0) > 0:
            st.markdown("### 📊 Generation Statistics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Queries", gen_stats['total_queries'])
            
            with col2:
                success_rate = gen_stats['successful_generations'] / gen_stats['total_queries']
                st.metric("Success Rate", f"{success_rate*100:.1f}%")
            
            with col3:
                st.metric("RAG Enhanced", f"{gen_stats.get('rag_enhancement_rate', 0)*100:.1f}%")
            
            with col4:
                st.metric("Avg Time", f"{gen_stats.get('avg_time', 0):.2f}s")
            
            # RAG-specific statistics
            if 'rag_stats' in gen_stats:
                rag_stats = gen_stats['rag_stats']
                st.markdown("### 🔍 RAG Statistics")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Retrieval Time", f"{rag_stats.get('avg_retrieval_time', 0):.3f}s")
                
                with col2:
                    st.metric("LLM Formatting", f"{rag_stats.get('llm_formatting_rate', 0)*100:.1f}%")
                
                with col3:
                    st.metric("Enhancement Rate", f"{rag_stats.get('rag_enhancement_rate', 0)*100:.1f}%")
    
    def run(self):
        """Run the Streamlit application."""
        # Render header
        self.render_header()
        
        # Render sidebar
        self.render_sidebar()
        
        # Main content tabs
        tab1, tab2, tab3 = st.tabs(["🔍 Query Interface", "🤖 RAG Dashboard", "🗄️ Database Explorer"])
        
        with tab1:
            self.render_main_interface()
        
        with tab2:
            self.render_rag_dashboard()
        
        with tab3:
            self.database_explorer.render()

def main():
    """Main application entry point."""
    app = RAGEnhancedClinicalNLQApp()
    app.run()

if __name__ == "__main__":
    main()