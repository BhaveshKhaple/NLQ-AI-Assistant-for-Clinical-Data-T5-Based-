#!/usr/bin/env python3
"""
Clinical NLQ Assistant - Main Application Launcher
Entry point for the Streamlit web application.
"""

import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))

# Set environment variables
if not os.getenv('DB_PASSWORD'):
    os.environ['DB_PASSWORD'] = ''

# Import and run the Streamlit app
from src.ui.streamlit_app import main

if __name__ == "__main__":
    main()