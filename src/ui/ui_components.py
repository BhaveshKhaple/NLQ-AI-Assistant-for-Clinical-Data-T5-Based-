#!/usr/bin/env python3
"""
UI Components
Reusable UI components and utilities for the Streamlit interface.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import json

class UIComponents:
    """
    Collection of reusable UI components for the Clinical NLQ Streamlit application.
    """
    
    def __init__(self):
        """Initialize UI components."""
        self.theme_colors = {
            'primary': '#1f77b4',
            'success': '#2ca02c',
            'warning': '#ff7f0e',
            'error': '#d62728',
            'info': '#17becf',
            'secondary': '#7f7f7f'
        }
    
    def render_status_indicator(self, 
                              status: str, 
                              label: str, 
                              details: Optional[str] = None) -> None:
        """
        Render a status indicator with color coding.
        
        Args:
            status: Status type ('success', 'warning', 'error', 'info')
            label: Status label
            details: Optional additional details
        """
        status_config = {
            'success': {'icon': '🟢', 'method': st.success},
            'warning': {'icon': '🟡', 'method': st.warning},
            'error': {'icon': '🔴', 'method': st.error},
            'info': {'icon': '🔵', 'method': st.info}
        }
        
        config = status_config.get(status, status_config['info'])
        message = f"{config['icon']} {label}"
        
        if details:
            message += f" - {details}"
        
        config['method'](message)
    
    def render_metric_card(self, 
                          title: str, 
                          value: Union[str, int, float], 
                          delta: Optional[Union[str, int, float]] = None,
                          delta_color: str = 'normal',
                          help_text: Optional[str] = None) -> None:
        """
        Render a metric card with optional delta.
        
        Args:
            title: Metric title
            value: Metric value
            delta: Optional delta value
            delta_color: Delta color ('normal', 'inverse', 'off')
            help_text: Optional help text
        """
        st.metric(
            label=title,
            value=value,
            delta=delta,
            delta_color=delta_color,
            help=help_text
        )
    
    def render_progress_bar(self, 
                           progress: float, 
                           label: str,
                           show_percentage: bool = True) -> None:
        """
        Render a progress bar with label.
        
        Args:
            progress: Progress value (0.0 to 1.0)
            label: Progress label
            show_percentage: Whether to show percentage
        """
        if show_percentage:
            st.text(f"{label}: {progress:.1%}")
        else:
            st.text(label)
        
        st.progress(progress)
    
    def render_data_table(self, 
                         data: Union[pd.DataFrame, List[Dict], Dict],
                         title: Optional[str] = None,
                         max_rows: int = 100,
                         show_download: bool = True,
                         show_stats: bool = False) -> None:
        """
        Render a data table with optional features.
        
        Args:
            data: Data to display
            title: Optional table title
            max_rows: Maximum rows to display
            show_download: Whether to show download button
            show_stats: Whether to show basic statistics
        """
        if title:
            st.subheader(title)
        
        # Convert data to DataFrame if needed
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            df = data
        
        if df.empty:
            st.info("📭 No data to display")
            return
        
        # Limit rows for display
        if len(df) > max_rows:
            st.warning(f"⚠️ Showing first {max_rows} rows of {len(df)} total rows")
            display_df = df.head(max_rows)
        else:
            display_df = df
        
        # Display table
        st.dataframe(display_df, use_container_width=True)
        
        # Show basic statistics for numeric columns
        if show_stats:
            numeric_cols = display_df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                with st.expander("📊 Basic Statistics"):
                    st.dataframe(display_df[numeric_cols].describe())
        
        # Download button
        if show_download:
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv_data,
                file_name=f"data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    def render_json_viewer(self, 
                          data: Dict[str, Any],
                          title: Optional[str] = None,
                          expanded: bool = False) -> None:
        """
        Render a JSON viewer with optional expansion.
        
        Args:
            data: JSON data to display
            title: Optional title
            expanded: Whether to show expanded by default
        """
        if title:
            if expanded:
                st.subheader(title)
                st.json(data)
            else:
                with st.expander(title):
                    st.json(data)
        else:
            st.json(data)
    
    def render_code_block(self, 
                         code: str,
                         language: str = 'sql',
                         title: Optional[str] = None,
                         show_copy: bool = True) -> None:
        """
        Render a code block with syntax highlighting.
        
        Args:
            code: Code to display
            language: Programming language for syntax highlighting
            title: Optional title
            show_copy: Whether to show copy button (not implemented in Streamlit)
        """
        if title:
            st.subheader(title)
        
        st.code(code, language=language)
        
        if show_copy:
            st.caption("💡 You can select and copy the code above")
    
    def render_timeline_chart(self, 
                             data: List[Dict[str, Any]],
                             x_field: str,
                             y_field: str,
                             color_field: Optional[str] = None,
                             title: str = "Timeline Chart") -> None:
        """
        Render a timeline chart using Plotly.
        
        Args:
            data: Data for the chart
            x_field: Field for x-axis (usually timestamp)
            y_field: Field for y-axis
            color_field: Optional field for color coding
            title: Chart title
        """
        if not data:
            st.info("📭 No data for timeline chart")
            return
        
        df = pd.DataFrame(data)
        
        if color_field and color_field in df.columns:
            fig = px.scatter(
                df, 
                x=x_field, 
                y=y_field,
                color=color_field,
                title=title,
                hover_data=list(df.columns)
            )
        else:
            fig = px.scatter(
                df, 
                x=x_field, 
                y=y_field,
                title=title,
                hover_data=list(df.columns)
            )
        
        fig.update_layout(
            xaxis_title=x_field.replace('_', ' ').title(),
            yaxis_title=y_field.replace('_', ' ').title(),
            hovermode='closest'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_performance_chart(self, 
                               performance_data: List[Dict[str, Any]],
                               title: str = "Performance Metrics") -> None:
        """
        Render performance metrics chart.
        
        Args:
            performance_data: Performance data
            title: Chart title
        """
        if not performance_data:
            st.info("📭 No performance data available")
            return
        
        df = pd.DataFrame(performance_data)
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Processing Time', 'Rows Returned', 'Success Rate', 'Query Length'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Processing time over time
        if 'processing_time' in df.columns and 'timestamp' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['processing_time'],
                    mode='lines+markers',
                    name='Processing Time (s)',
                    line=dict(color=self.theme_colors['primary'])
                ),
                row=1, col=1
            )
        
        # Rows returned over time
        if 'rows_returned' in df.columns and 'timestamp' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['rows_returned'],
                    mode='lines+markers',
                    name='Rows Returned',
                    line=dict(color=self.theme_colors['success'])
                ),
                row=1, col=2
            )
        
        # Success rate (if available)
        if 'success' in df.columns:
            success_rate = df['success'].rolling(window=10, min_periods=1).mean()
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=success_rate,
                    mode='lines',
                    name='Success Rate',
                    line=dict(color=self.theme_colors['warning'])
                ),
                row=2, col=1
            )
        
        # Query length distribution
        if 'nlq_length' in df.columns:
            fig.add_trace(
                go.Histogram(
                    x=df['nlq_length'],
                    name='Query Length Distribution',
                    marker_color=self.theme_colors['info']
                ),
                row=2, col=2
            )
        
        fig.update_layout(
            title=title,
            showlegend=False,
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_error_summary(self, 
                           error_data: Dict[str, Any],
                           title: str = "Error Summary") -> None:
        """
        Render error summary with charts.
        
        Args:
            error_data: Error summary data
            title: Summary title
        """
        st.subheader(title)
        
        if error_data.get('total_errors', 0) == 0:
            st.success("🎉 No errors recorded!")
            return
        
        # Error metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            self.render_metric_card(
                "Total Errors",
                error_data.get('total_errors', 0),
                help_text="Total number of errors encountered"
            )
        
        with col2:
            error_rate = error_data.get('error_rate', 0)
            self.render_metric_card(
                "Error Rate",
                f"{error_rate:.1%}",
                help_text="Percentage of operations that resulted in errors"
            )
        
        with col3:
            most_common = error_data.get('most_common_error', 'None')
            st.metric(
                "Most Common Error",
                most_common,
                help="Most frequently occurring error type"
            )
        
        # Error types breakdown
        error_types = error_data.get('error_types', {})
        if error_types:
            st.subheader("🔍 Error Types Breakdown")
            
            # Create pie chart
            fig = px.pie(
                values=list(error_types.values()),
                names=list(error_types.keys()),
                title="Error Distribution by Type"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Error types table
            error_df = pd.DataFrame([
                {'Error Type': k, 'Count': v, 'Percentage': f"{v/sum(error_types.values()):.1%}"}
                for k, v in error_types.items()
            ])
            
            st.dataframe(error_df, use_container_width=True)
    
    def render_query_examples(self, 
                            examples: List[Dict[str, Any]],
                            on_example_click: callable = None) -> None:
        """
        Render query examples with categories.
        
        Args:
            examples: List of example queries organized by category
            on_example_click: Callback function when example is clicked
        """
        st.subheader("💡 Example Queries")
        
        for category in examples:
            with st.expander(f"📂 {category['category']}"):
                for query in category['queries']:
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.text(query)
                    
                    with col2:
                        if st.button("▶️", key=f"example_{query}", help="Use this query"):
                            if on_example_click:
                                on_example_click(query)
    
    def render_session_info(self, 
                          session_data: Dict[str, Any],
                          title: str = "Session Information") -> None:
        """
        Render session information panel.
        
        Args:
            session_data: Session data
            title: Panel title
        """
        with st.expander(title):
            col1, col2 = st.columns(2)
            
            with col1:
                st.text(f"Session ID: {session_data.get('session_id', 'Unknown')}")
                st.text(f"User ID: {session_data.get('user_id', 'Anonymous')}")
                st.text(f"Created: {session_data.get('created_at', 'Unknown')}")
            
            with col2:
                st.text(f"Queries: {session_data.get('query_count', 0)}")
                st.text(f"Success: {session_data.get('success_count', 0)}")
                st.text(f"Errors: {session_data.get('error_count', 0)}")
    
    def render_loading_spinner(self, 
                             message: str = "Processing...",
                             show_progress: bool = False,
                             progress_value: float = 0.0) -> None:
        """
        Render loading spinner with optional progress bar.
        
        Args:
            message: Loading message
            show_progress: Whether to show progress bar
            progress_value: Progress value (0.0 to 1.0)
        """
        with st.spinner(message):
            if show_progress:
                st.progress(progress_value)
    
    def render_alert_box(self, 
                        message: str,
                        alert_type: str = 'info',
                        dismissible: bool = False,
                        key: Optional[str] = None) -> bool:
        """
        Render an alert box with different types.
        
        Args:
            message: Alert message
            alert_type: Type of alert ('success', 'info', 'warning', 'error')
            dismissible: Whether the alert can be dismissed
            key: Optional key for dismissible alerts
            
        Returns:
            True if alert is visible, False if dismissed
        """
        if dismissible and key:
            if f"dismissed_{key}" in st.session_state:
                return False
        
        alert_methods = {
            'success': st.success,
            'info': st.info,
            'warning': st.warning,
            'error': st.error
        }
        
        method = alert_methods.get(alert_type, st.info)
        
        if dismissible and key:
            col1, col2 = st.columns([10, 1])
            with col1:
                method(message)
            with col2:
                if st.button("✕", key=f"dismiss_{key}", help="Dismiss"):
                    st.session_state[f"dismissed_{key}"] = True
                    st.rerun()
        else:
            method(message)
        
        return True
    
    def render_collapsible_section(self, 
                                 title: str,
                                 content_func: callable,
                                 expanded: bool = False,
                                 key: Optional[str] = None) -> None:
        """
        Render a collapsible section with dynamic content.
        
        Args:
            title: Section title
            content_func: Function to render content
            expanded: Whether section is expanded by default
            key: Optional key for the expander
        """
        with st.expander(title, expanded=expanded):
            content_func()
    
    def render_tabs_container(self, 
                            tabs_config: List[Dict[str, Any]],
                            default_tab: int = 0) -> None:
        """
        Render a tabs container with dynamic content.
        
        Args:
            tabs_config: List of tab configurations
            default_tab: Default active tab index
        """
        tab_names = [tab['name'] for tab in tabs_config]
        tabs = st.tabs(tab_names)
        
        for i, (tab, config) in enumerate(zip(tabs, tabs_config)):
            with tab:
                if 'content_func' in config:
                    config['content_func']()
                elif 'content' in config:
                    st.write(config['content'])
    
    def render_sidebar_filters(self, 
                             filters_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Render sidebar filters and return selected values.
        
        Args:
            filters_config: Configuration for filters
            
        Returns:
            Dictionary of selected filter values
        """
        st.sidebar.header("🔍 Filters")
        
        selected_filters = {}
        
        for filter_name, filter_config in filters_config.items():
            filter_type = filter_config.get('type', 'text')
            label = filter_config.get('label', filter_name)
            
            if filter_type == 'selectbox':
                selected_filters[filter_name] = st.sidebar.selectbox(
                    label,
                    options=filter_config.get('options', []),
                    index=filter_config.get('default_index', 0)
                )
            
            elif filter_type == 'multiselect':
                selected_filters[filter_name] = st.sidebar.multiselect(
                    label,
                    options=filter_config.get('options', []),
                    default=filter_config.get('default', [])
                )
            
            elif filter_type == 'slider':
                selected_filters[filter_name] = st.sidebar.slider(
                    label,
                    min_value=filter_config.get('min_value', 0),
                    max_value=filter_config.get('max_value', 100),
                    value=filter_config.get('default_value', 50)
                )
            
            elif filter_type == 'date_range':
                col1, col2 = st.sidebar.columns(2)
                with col1:
                    start_date = st.date_input(
                        f"{label} Start",
                        value=filter_config.get('default_start', datetime.now().date())
                    )
                with col2:
                    end_date = st.date_input(
                        f"{label} End",
                        value=filter_config.get('default_end', datetime.now().date())
                    )
                selected_filters[filter_name] = (start_date, end_date)
            
            elif filter_type == 'checkbox':
                selected_filters[filter_name] = st.sidebar.checkbox(
                    label,
                    value=filter_config.get('default', False)
                )
            
            else:  # text input
                selected_filters[filter_name] = st.sidebar.text_input(
                    label,
                    value=filter_config.get('default', '')
                )
        
        return selected_filters