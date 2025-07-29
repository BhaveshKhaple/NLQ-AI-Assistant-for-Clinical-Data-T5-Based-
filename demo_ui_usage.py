#!/usr/bin/env python3
"""
Clinical NLQ UI Demo Script
Demonstrates how to use the Streamlit web interface programmatically.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

def check_requirements():
    """Check if all requirements are met."""
    print("🔍 Checking requirements...")
    
    # Check if streamlit is installed
    try:
        import streamlit
        print(f"✅ Streamlit installed: {streamlit.__version__}")
    except ImportError:
        print("❌ Streamlit not installed. Run: pip install streamlit")
        return False
    
    # Check if app.py exists
    app_file = Path(__file__).parent / "app.py"
    if app_file.exists():
        print("✅ Application file found: app.py")
    else:
        print("❌ Application file not found: app.py")
        return False
    
    # Check if config exists
    config_file = Path(__file__).parent / "config" / "config.yaml"
    if config_file.exists():
        print("✅ Configuration file found: config/config.yaml")
    else:
        print("⚠️ Configuration file not found, using defaults")
    
    # Check database password
    if not os.getenv('DB_PASSWORD'):
        print("⚠️ DB_PASSWORD not set, using empty password")
        os.environ['DB_PASSWORD'] = ''
    else:
        print("✅ Database password configured")
    
    return True

def launch_application():
    """Launch the Streamlit application."""
    print("\n🚀 Launching Clinical NLQ Assistant...")
    print("=" * 50)
    
    app_path = Path(__file__).parent / "app.py"
    
    try:
        # Launch streamlit
        print("Starting Streamlit server...")
        print("📱 The application will open in your default browser")
        print("🌐 URL: http://localhost:8501")
        print("\n💡 Usage Tips:")
        print("   • Try example queries from the sidebar")
        print("   • Use natural language like 'How many patients do we have?'")
        print("   • Check the Analytics tab for session statistics")
        print("   • Use Ctrl+C to stop the server")
        print("\n" + "=" * 50)
        
        # Run streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(app_path),
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
        
    except KeyboardInterrupt:
        print("\n\n🛑 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Error launching application: {e}")
        print("\n🔧 Troubleshooting:")
        print("   • Make sure all dependencies are installed: pip install -r requirements.txt")
        print("   • Check if port 8501 is available")
        print("   • Verify database connection settings")

def show_usage_examples():
    """Show usage examples for the web interface."""
    print("\n📚 Usage Examples")
    print("=" * 50)
    
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
        print(f"\n📂 {example['category']}:")
        for i, query in enumerate(example['queries'], 1):
            print(f"   {i}. {query}")
    
    print(f"\n💡 Tips:")
    print("   • Use natural language - no need for SQL knowledge")
    print("   • Be specific about what data you want")
    print("   • Try different output formats (table, JSON, CSV)")
    print("   • Check the generated SQL to understand the query")

def show_interface_features():
    """Show interface features and capabilities."""
    print("\n🎨 Interface Features")
    print("=" * 50)
    
    features = [
        {
            "section": "Query Interface",
            "features": [
                "Natural language input with validation",
                "Advanced options for SQL generation",
                "Multiple output formats (table, JSON, CSV, summary)",
                "Real-time processing with progress indicators"
            ]
        },
        {
            "section": "Results Display",
            "features": [
                "Interactive data tables with sorting",
                "JSON viewer with syntax highlighting",
                "CSV export for spreadsheet analysis",
                "Statistical summary and insights"
            ]
        },
        {
            "section": "Analytics Dashboard",
            "features": [
                "Session statistics and performance metrics",
                "Query history with success/failure tracking",
                "Response time analysis and trends",
                "Error analysis and troubleshooting"
            ]
        },
        {
            "section": "Settings & Preferences",
            "features": [
                "Show/hide generated SQL queries",
                "Customize output format preferences",
                "Adjust display limits and pagination",
                "Configure advanced query parameters"
            ]
        }
    ]
    
    for feature_group in features:
        print(f"\n🔧 {feature_group['section']}:")
        for feature in feature_group['features']:
            print(f"   • {feature}")

def main():
    """Main demo function."""
    print("🏥 Clinical NLQ Assistant - Web Interface Demo")
    print("=" * 60)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Requirements check failed. Please fix the issues above.")
        return 1
    
    print("\n✅ All requirements met!")
    
    # Show usage information
    show_interface_features()
    show_usage_examples()
    
    # Ask user if they want to launch
    print("\n" + "=" * 60)
    response = input("🚀 Would you like to launch the application now? (y/n): ").lower().strip()
    
    if response in ['y', 'yes']:
        launch_application()
    else:
        print("\n📝 To launch manually, run:")
        print("   streamlit run app.py")
        print("\n🌐 Then open: http://localhost:8501")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)