#!/usr/bin/env python3
"""
RAG-Enhanced Clinical NLQ App Launcher
Launch the RAG-enhanced Streamlit application.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Launch the RAG-enhanced Streamlit app."""
    print("🚀 Starting RAG-Enhanced Clinical NLQ Assistant")
    print("=" * 60)
    
    # Get the project root directory
    project_root = Path(__file__).parent
    app_path = project_root / "src" / "ui" / "rag_streamlit_app.py"
    
    # Check if the app file exists
    if not app_path.exists():
        print(f"❌ Error: App file not found at {app_path}")
        return
    
    # Set environment variables
    os.environ['PYTHONPATH'] = str(project_root / "src")
    
    print(f"📁 Project Root: {project_root}")
    print(f"🎯 App Path: {app_path}")
    print(f"🔧 Python Path: {os.environ.get('PYTHONPATH', 'Not set')}")
    print()
    
    # Launch Streamlit
    try:
        print("🌐 Launching Streamlit application...")
        print("📱 The app will open in your default web browser")
        print("🔗 URL: http://localhost:8501")
        print()
        print("💡 Features available:")
        print("   • RAG-enhanced query processing")
        print("   • Semantic similarity search")
        print("   • Training example retrieval")
        print("   • Advanced T5 model inference")
        print("   • Real-time performance metrics")
        print()
        print("⏹️  Press Ctrl+C to stop the application")
        print("=" * 60)
        
        # Run streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(app_path),
            "--server.port=8501",
            "--server.address=localhost",
            "--browser.gatherUsageStats=false"
        ])
        
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Error launching application: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure all dependencies are installed: pip install -r requirements.txt")
        print("   2. Check that the model files are present in models/trained/")
        print("   3. Verify database connection settings in .env file")

if __name__ == "__main__":
    main()