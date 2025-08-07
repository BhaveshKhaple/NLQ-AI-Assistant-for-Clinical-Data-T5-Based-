#!/usr/bin/env python3
"""
Start Gemini RAG API Server
Launcher script for the Gemini-enhanced RAG Clinical NLQ API server.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        'fastapi',
        'uvicorn',
        'google-generativeai',
        'sentence-transformers',
        'torch',
        'transformers'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Install missing packages with:")
        print("   pip install -r requirements_api.txt")
        print("   or")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_environment():
    """Check environment variables."""
    required_env_vars = [
        'GEMINI_API_KEY',  # or GOOGLE_API_KEY
        'DB_HOST',
        'DB_NAME',
        'DB_USERNAME',
        'DB_PASSWORD',
        'DB_SCHEMA'
    ]
    
    missing_vars = []
    
    # Check Gemini API key (either GEMINI_API_KEY or GOOGLE_API_KEY)
    if not os.getenv('GEMINI_API_KEY') and not os.getenv('GOOGLE_API_KEY'):
        missing_vars.append('GEMINI_API_KEY (or GOOGLE_API_KEY)')
    
    # Check database variables
    for var in required_env_vars[1:]:  # Skip GEMINI_API_KEY as we checked it above
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("⚠️ Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n🔧 Set environment variables in .env file or system environment")
        return False
    
    return True

def main():
    """Start the API server."""
    print("🚀 Starting Gemini RAG Clinical NLQ API Server")
    print("=" * 60)
    
    # Check dependencies
    print("📦 Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    print("✅ All dependencies available")
    
    # Check environment
    print("🔧 Checking environment...")
    if not check_environment():
        print("⚠️ Some environment variables are missing, but continuing...")
        print("   (API will show warnings for missing services)")
    else:
        print("✅ Environment configured")
    
    # Get script directory
    script_dir = Path(__file__).parent
    api_script = script_dir / "src" / "api" / "gemini_rag_api.py"
    
    if not api_script.exists():
        print(f"❌ API script not found: {api_script}")
        sys.exit(1)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Start Gemini RAG API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes (default: 1)")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"], help="Log level")
    
    args = parser.parse_args()
    
    # Build command
    cmd = [
        sys.executable, "-m", "uvicorn",
        "src.api.gemini_rag_api:app",
        "--host", args.host,
        "--port", str(args.port),
        "--log-level", args.log_level
    ]
    
    if args.reload:
        cmd.append("--reload")
    
    if args.workers > 1:
        cmd.extend(["--workers", str(args.workers)])
    
    print(f"🌐 Starting server on http://{args.host}:{args.port}")
    print(f"📚 API documentation: http://{args.host}:{args.port}/docs")
    print(f"🔍 Health check: http://{args.host}:{args.port}/health")
    print("=" * 60)
    
    try:
        # Change to project directory
        os.chdir(script_dir)
        
        # Start the server
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()