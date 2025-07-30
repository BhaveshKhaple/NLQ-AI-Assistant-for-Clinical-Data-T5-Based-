#!/usr/bin/env python3
"""
Database Explorer UI Component
Streamlit component for exploring database structure and data.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Add src to path for imports
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from database.database_viewer import DatabaseViewer

class DatabaseExplorer:
    """Database explorer UI component for Streamlit."""
    
    def __init__(self):
        """Initialize the database explorer."""
        self.db_viewer = None
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state variables."""
        if 'db_explorer_initialized' not in st.session_state:
            st.session_state.db_explorer_initialized = False
        if 'db_connection_status' not in st.session_state:
            st.session_state.db_connection_status = False
        if 'selected_schema' not in st.session_state:
            st.session_state.selected_schema = 'clinical_data'
        if 'selected_table' not in st.session_state:
            st.session_state.selected_table = None
        if 'database_overview' not in st.session_state:
            st.session_state.database_overview = None
        if 'table_data_cache' not in st.session_state:
            st.session_state.table_data_cache = {}
        if 'db_viewer_instance' not in st.session_state:
            st.session_state.db_viewer_instance = None
    
    def _initialize_database_connection(self):
        """Initialize database connection."""
        if not st.session_state.db_explorer_initialized:
            try:
                self.db_viewer = DatabaseViewer()
                if self.db_viewer.connect():
                    st.session_state.db_explorer_initialized = True
                    st.session_state.db_connection_status = True
                    st.session_state.database_overview = self.db_viewer.get_database_overview()
                    return True
                else:
                    st.session_state.db_connection_status = False
                    return False
            except Exception as e:
                st.error(f"Failed to initialize database connection: {e}")
                return False
        else:
            # If already initialized but db_viewer is None, recreate it
            if self.db_viewer is None:
                self.db_viewer = DatabaseViewer()
                self.db_viewer.connect()
        return st.session_state.db_connection_status
    
    def _ensure_db_connection(self):
        """Ensure database connection is available."""
        # Always ensure we have a fresh connection for reliability
        if self.db_viewer is None:
            self.db_viewer = DatabaseViewer()
            if not self.db_viewer.connect():
                return False
        
        # Test the connection
        try:
            if not self.db_viewer.connection:
                self.db_viewer.connect()
        except:
            self.db_viewer = DatabaseViewer()
            if not self.db_viewer.connect():
                return False
        
        return True
    
    def render_database_overview(self):
        """Render database overview section."""
        st.header("📊 Database Overview")
        
        if not self._initialize_database_connection():
            st.error("❌ Cannot connect to database. Please check your connection settings.")
            return
        
        overview = st.session_state.database_overview
        if not overview:
            st.warning("No database overview available.")
            return
        
        # Connection status
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if overview['connection_status']:
                st.success("🟢 Connected")
            else:
                st.error("🔴 Disconnected")
        
        with col2:
            st.metric("Schemas", len(overview['schemas']))
        
        with col3:
            st.metric("Tables", overview['total_tables'])
        
        with col4:
            st.metric("Columns", overview['total_columns'])
        
        # Schema information
        if overview['schemas']:
            st.subheader("📁 Available Schemas")
            schema_df = pd.DataFrame(overview['schemas'])
            st.dataframe(schema_df, use_container_width=True)
    
    def render_table_explorer(self):
        """Render table explorer section."""
        st.header("🗂️ Table Explorer")
        
        if not st.session_state.db_connection_status:
            st.warning("Database connection required for table exploration.")
            return
        
        overview = st.session_state.database_overview
        if not overview or not overview.get('clinical_data_tables'):
            st.warning("No tables found in clinical_data schema.")
            return
        
        # Table selection
        tables = overview['clinical_data_tables']
        table_names = [table['table_name'] for table in tables]
        
        selected_table = st.selectbox(
            "Select a table to explore:",
            options=table_names,
            index=0 if table_names else None,
            key="table_selector"
        )
        
        if selected_table:
            st.session_state.selected_table = selected_table
            self._render_table_details(selected_table)
    
    def _render_table_details(self, table_name: str):
        """Render detailed information for a selected table."""
        st.subheader(f"📋 Table: {table_name}")
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📝 Columns", "🔍 Sample Data", "📈 Statistics"])
        
        with tab1:
            self._render_table_overview(table_name)
        
        with tab2:
            self._render_table_columns(table_name)
        
        with tab3:
            self._render_sample_data(table_name)
        
        with tab4:
            self._render_table_statistics(table_name)
    
    def _render_table_overview(self, table_name: str):
        """Render table overview information."""
        # Get table metadata
        tables = st.session_state.database_overview['clinical_data_tables']
        table_info = next((t for t in tables if t['table_name'] == table_name), None)
        
        if table_info:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Columns", table_info['column_count'])
            
            with col2:
                st.metric("Estimated Rows", f"{table_info['estimated_row_count']:,}")
            
            with col3:
                st.metric("Table Size", table_info['table_size'])
        
        # Show relationships
        relationships = st.session_state.database_overview.get('relationships', [])
        table_relationships = [
            rel for rel in relationships 
            if rel['source_table'] == table_name or rel['target_table'] == table_name
        ]
        
        if table_relationships:
            st.subheader("🔗 Relationships")
            rel_df = pd.DataFrame(table_relationships)
            st.dataframe(rel_df, use_container_width=True)
    
    def _render_table_columns(self, table_name: str):
        """Render table column information."""
        if not self._ensure_db_connection():
            st.error("Cannot connect to database")
            return
        
        try:
            with st.spinner(f"Loading column information for {table_name}..."):
                columns = self.db_viewer.get_table_columns(table_name)
            
            st.success(f"✅ Found {len(columns)} columns for table {table_name}")
            
            if columns:
                # Create a more readable DataFrame
                column_data = []
                for col in columns:
                    try:
                        data_type = col['data_type']
                        if col.get('character_maximum_length'):
                            data_type += f"({col['character_maximum_length']})"
                        elif col.get('numeric_precision'):
                            if col.get('numeric_scale'):
                                data_type += f"({col['numeric_precision']},{col['numeric_scale']})"
                            else:
                                data_type += f"({col['numeric_precision']})"
                        
                        column_data.append({
                            'Column': col.get('column_name', 'Unknown'),
                            'Type': data_type,
                            'Nullable': '✓' if col.get('is_nullable') == 'YES' else '✗',
                            'Default': col.get('column_default') or '',
                            'Constraint': col.get('constraint_type') or '',
                            'References': f"{col.get('foreign_table_name', '')}.{col.get('foreign_column_name', '')}" 
                                        if col.get('foreign_table_name') else ''
                        })
                    except Exception as e:
                        st.error(f"Error processing column {col}: {e}")
                        continue
                
                if column_data:
                    columns_df = pd.DataFrame(column_data)
                    st.dataframe(columns_df, use_container_width=True)
                    
                    # Column type distribution
                    try:
                        type_counts = pd.DataFrame(columns).groupby('data_type').size().reset_index(name='count')
                        if len(type_counts) > 1:
                            fig = px.pie(type_counts, values='count', names='data_type', 
                                       title="Column Type Distribution")
                            st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.warning(f"Could not create type distribution chart: {e}")
                else:
                    st.warning("No valid column data could be processed.")
            else:
                st.warning("No column information available.")
        except Exception as e:
            st.error(f"Error loading column information: {e}")
            import traceback
            st.code(traceback.format_exc())
    
    def _render_sample_data(self, table_name: str):
        """Render sample data from the table."""
        if not self._ensure_db_connection():
            st.error("Cannot connect to database")
            return
        
        # Sample size selector
        sample_size = st.slider("Sample size:", min_value=5, max_value=100, value=10, step=5)
        
        # Get sample data
        cache_key = f"{table_name}_{sample_size}"
        if cache_key not in st.session_state.table_data_cache:
            with st.spinner(f"Loading sample data from {table_name}..."):
                sample_data = self.db_viewer.get_table_sample_data(table_name, limit=sample_size)
                st.session_state.table_data_cache[cache_key] = sample_data
        
        sample_data = st.session_state.table_data_cache[cache_key]
        
        if not sample_data.empty:
            st.subheader(f"📄 Sample Data ({len(sample_data)} rows)")
            st.dataframe(sample_data, use_container_width=True)
            
            # Download option
            csv = sample_data.to_csv(index=False)
            st.download_button(
                label="📥 Download Sample Data as CSV",
                data=csv,
                file_name=f"{table_name}_sample.csv",
                mime="text/csv"
            )
        else:
            st.warning("No sample data available or table is empty.")
    
    def _render_table_statistics(self, table_name: str):
        """Render table statistics."""
        if not self._ensure_db_connection():
            st.error("Cannot connect to database")
            return
        
        with st.spinner("Calculating table statistics..."):
            stats = self.db_viewer.get_table_statistics(table_name)
        
        if stats:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Rows", f"{stats['row_count']:,}")
            
            with col2:
                st.metric("Table Size", stats['table_size'])
            
            with col3:
                st.metric("Data Size", stats['data_size'])
            
            # Column statistics
            if stats.get('column_statistics'):
                st.subheader("📊 Numeric Column Statistics")
                
                for col_name, col_stats in stats['column_statistics'].items():
                    with st.expander(f"📈 {col_name}"):
                        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
                        
                        with stat_col1:
                            st.metric("Min", f"{col_stats['min_val']:.2f}" if col_stats['min_val'] is not None else "N/A")
                        
                        with stat_col2:
                            st.metric("Max", f"{col_stats['max_val']:.2f}" if col_stats['max_val'] is not None else "N/A")
                        
                        with stat_col3:
                            st.metric("Average", f"{col_stats['avg_val']:.2f}" if col_stats['avg_val'] is not None else "N/A")
                        
                        with stat_col4:
                            st.metric("Distinct Values", f"{col_stats['distinct_count']:,}" if col_stats['distinct_count'] is not None else "N/A")
        else:
            st.warning("Unable to calculate table statistics.")
    
    def render_custom_query(self):
        """Render custom query interface."""
        st.header("🔍 Custom Query Explorer")
        
        if not st.session_state.db_connection_status:
            st.warning("Database connection required for custom queries.")
            return
        
        st.info("💡 **Tip**: Use this section to run custom SQL queries to explore your data before using the NLQ interface.")
        
        # Query input
        query = st.text_area(
            "Enter your SQL query:",
            placeholder="SELECT * FROM clinical_data.patients LIMIT 10;",
            height=150,
            help="Write SQL queries to explore your database. Be careful with large result sets."
        )
        
        # Query options
        col1, col2 = st.columns(2)
        
        with col1:
            limit_results = st.checkbox("Limit results", value=True)
            if limit_results:
                result_limit = st.number_input("Max rows to return:", min_value=1, max_value=1000, value=100)
        
        with col2:
            show_execution_time = st.checkbox("Show execution time", value=True)
        
        # Execute query
        if st.button("🚀 Execute Query", type="primary"):
            if query.strip():
                self._execute_custom_query(query.strip(), limit_results, result_limit if limit_results else None, show_execution_time)
            else:
                st.warning("Please enter a query.")
    
    def _execute_custom_query(self, query: str, limit_results: bool, result_limit: Optional[int], show_execution_time: bool):
        """Execute a custom SQL query."""
        if not self.db_viewer:
            return
        
        # Add LIMIT if requested and not already present
        if limit_results and result_limit and 'LIMIT' not in query.upper():
            query = f"{query.rstrip(';')} LIMIT {result_limit};"
        
        try:
            import time
            start_time = time.time()
            
            with st.spinner("Executing query..."):
                result_df = self.db_viewer.execute_custom_query(query)
            
            execution_time = time.time() - start_time
            
            if not result_df.empty:
                st.success(f"✅ Query executed successfully! Returned {len(result_df)} rows.")
                
                if show_execution_time:
                    st.info(f"⏱️ Execution time: {execution_time:.3f} seconds")
                
                # Display results
                st.subheader("📊 Query Results")
                st.dataframe(result_df, use_container_width=True)
                
                # Download option
                csv = result_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Results as CSV",
                    data=csv,
                    file_name="query_results.csv",
                    mime="text/csv"
                )
                
                # Basic statistics if numeric columns exist
                numeric_columns = result_df.select_dtypes(include=['number']).columns
                if len(numeric_columns) > 0:
                    with st.expander("📈 Quick Statistics"):
                        st.dataframe(result_df[numeric_columns].describe(), use_container_width=True)
            else:
                st.warning("Query executed successfully but returned no results.")
                if show_execution_time:
                    st.info(f"⏱️ Execution time: {execution_time:.3f} seconds")
        
        except Exception as e:
            st.error(f"❌ Query execution failed: {e}")
    
    def render_schema_diagram(self):
        """Render a visual schema diagram."""
        st.header("🗺️ Database Schema Diagram")
        
        if not st.session_state.db_connection_status:
            st.warning("Database connection required for schema diagram.")
            return
        
        relationships = st.session_state.database_overview.get('relationships', [])
        tables = st.session_state.database_overview.get('clinical_data_tables', [])
        
        if not relationships or not tables:
            st.warning("No relationship data available for schema diagram.")
            return
        
        # Create a network-style diagram using plotly
        import networkx as nx
        
        # Create graph
        G = nx.Graph()
        
        # Add nodes (tables)
        for table in tables:
            G.add_node(table['table_name'], 
                      size=min(table['column_count'] * 2, 50),
                      rows=table['estimated_row_count'])
        
        # Add edges (relationships)
        for rel in relationships:
            G.add_edge(rel['source_table'], rel['target_table'])
        
        # Generate layout
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        # Create plotly figure
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(x=edge_x, y=edge_y,
                               line=dict(width=2, color='#888'),
                               hoverinfo='none',
                               mode='lines')
        
        node_x = []
        node_y = []
        node_text = []
        node_size = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(f"{node}<br>Columns: {G.nodes[node]['size']//2}<br>Rows: {G.nodes[node]['rows']:,}")
            node_size.append(max(G.nodes[node]['size'], 20))
        
        node_trace = go.Scatter(x=node_x, y=node_y,
                               mode='markers+text',
                               hoverinfo='text',
                               text=[node for node in G.nodes()],
                               textposition="middle center",
                               hovertext=node_text,
                               marker=dict(size=node_size,
                                         color='lightblue',
                                         line=dict(width=2, color='darkblue')))
        
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title=dict(text='Database Schema Relationships', font=dict(size=16)),
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           annotations=[ dict(
                               text="Hover over nodes for details",
                               showarrow=False,
                               xref="paper", yref="paper",
                               x=0.005, y=-0.002,
                               xanchor="left", yanchor="bottom",
                               font=dict(color="#888", size=12)
                           )],
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_full_explorer(self):
        """Render the complete database explorer interface."""
        st.title("🗄️ Database Explorer")
        st.markdown("Explore your clinical database structure and data before using the NLQ interface.")
        
        # Create main tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview", 
            "🗂️ Tables", 
            "🔍 Custom Query", 
            "🗺️ Schema Diagram",
            "💡 Query Examples"
        ])
        
        with tab1:
            self.render_database_overview()
        
        with tab2:
            self.render_table_explorer()
        
        with tab3:
            self.render_custom_query()
        
        with tab4:
            self.render_schema_diagram()
        
        with tab5:
            self._render_query_examples()
    
    def _render_query_examples(self):
        """Render example queries to help users understand the data."""
        st.header("💡 Example Queries")
        st.markdown("Here are some example queries to help you understand your clinical data:")
        
        examples = [
            {
                "title": "Patient Demographics",
                "description": "Get basic patient information",
                "query": "SELECT gender, race, COUNT(*) as patient_count\nFROM clinical_data.patients\nGROUP BY gender, race\nORDER BY patient_count DESC;"
            },
            {
                "title": "Common Conditions",
                "description": "Find the most common medical conditions",
                "query": "SELECT description, COUNT(*) as condition_count\nFROM clinical_data.conditions\nGROUP BY description\nORDER BY condition_count DESC\nLIMIT 10;"
            },
            {
                "title": "Patient Age Distribution",
                "description": "Analyze patient age groups",
                "query": "SELECT \n  CASE \n    WHEN EXTRACT(YEAR FROM AGE(birth_date)) < 18 THEN 'Under 18'\n    WHEN EXTRACT(YEAR FROM AGE(birth_date)) BETWEEN 18 AND 65 THEN '18-65'\n    ELSE 'Over 65'\n  END as age_group,\n  COUNT(*) as patient_count\nFROM clinical_data.patients\nGROUP BY age_group;"
            },
            {
                "title": "Medication Usage",
                "description": "Most prescribed medications",
                "query": "SELECT description, COUNT(*) as prescription_count\nFROM clinical_data.medications\nGROUP BY description\nORDER BY prescription_count DESC\nLIMIT 10;"
            },
            {
                "title": "Healthcare Encounters",
                "description": "Encounter types and frequency",
                "query": "SELECT encounter_class, COUNT(*) as encounter_count\nFROM clinical_data.encounters\nGROUP BY encounter_class\nORDER BY encounter_count DESC;"
            }
        ]
        
        for example in examples:
            with st.expander(f"📋 {example['title']}"):
                st.markdown(f"**Description:** {example['description']}")
                st.code(example['query'], language='sql')
                
                if st.button(f"Run Query", key=f"run_{example['title']}"):
                    self._execute_custom_query(example['query'], True, 50, True)
    
    def cleanup(self):
        """Cleanup database connections."""
        if self.db_viewer:
            self.db_viewer.disconnect()