@echo off
echo 🏥 Clinical NLQ Assistant - Starting Application
echo ================================================

cd /d "%~dp0"

echo 📍 Current directory: %CD%
echo 🔍 Checking virtual environment...

if not exist "venv\Scripts\python.exe" (
    echo ❌ Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then install requirements: venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

echo ✅ Virtual environment found
echo 🚀 Starting Streamlit application...
echo.
echo 🌐 The application will open in your browser at: http://localhost:8503
echo 💡 Press Ctrl+C to stop the server
echo.

venv\Scripts\streamlit.exe run app.py --server.port 8503

echo.
echo 👋 Application stopped
pause