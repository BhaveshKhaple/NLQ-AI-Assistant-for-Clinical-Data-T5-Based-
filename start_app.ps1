#!/usr/bin/env powershell
# Clinical NLQ Assistant - PowerShell Startup Script

Write-Host "🏥 Clinical NLQ Assistant - Starting Application" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Change to script directory
Set-Location $PSScriptRoot

Write-Host "📍 Current directory: $(Get-Location)" -ForegroundColor Yellow
Write-Host "🔍 Checking virtual environment..." -ForegroundColor Yellow

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv venv" -ForegroundColor Red
    Write-Host "Then install requirements: venv\Scripts\pip install -r requirements.txt" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✅ Virtual environment found" -ForegroundColor Green
Write-Host "🚀 Starting Streamlit application..." -ForegroundColor Green
Write-Host ""
Write-Host "🌐 The application will open in your browser at: http://localhost:8503" -ForegroundColor Cyan
Write-Host "💡 Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

try {
    & "venv\Scripts\streamlit.exe" run app.py --server.port 8503
}
catch {
    Write-Host "❌ Error starting application: $_" -ForegroundColor Red
}
finally {
    Write-Host ""
    Write-Host "👋 Application stopped" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
}