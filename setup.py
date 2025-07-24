#!/usr/bin/env python3
"""
Clinical NLQ AI Assistant - Setup Script
=========================================

This script sets up the development environment for the Clinical Natural Language Query AI Assistant.
It handles virtual environment creation, dependency installation, and initial configuration.

Usage:
    python setup.py --help
    python setup.py --dev          # Development setup
    python setup.py --prod         # Production setup
    python setup.py --test         # Test environment setup
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
import yaml
import json

class SetupManager:
    """Manages the setup process for the Clinical NLQ AI Assistant."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.venv_path = self.project_root / "venv"
        self.config_path = self.project_root / "config" / "config.yaml"
        
    def create_virtual_environment(self):
        """Create a Python virtual environment."""
        print("Creating virtual environment...")
        try:
            subprocess.run([sys.executable, "-m", "venv", str(self.venv_path)], check=True)
            print(f"✓ Virtual environment created at {self.venv_path}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to create virtual environment: {e}")
            return False
        return True
    
    def install_dependencies(self, dev_mode=True):
        """Install Python dependencies."""
        print("Installing dependencies...")
        
        # Determine pip executable path
        if os.name == 'nt':  # Windows
            pip_path = self.venv_path / "Scripts" / "pip.exe"
            python_path = self.venv_path / "Scripts" / "python.exe"
        else:  # Unix/Linux/macOS
            pip_path = self.venv_path / "bin" / "pip"
            python_path = self.venv_path / "bin" / "python"
        
        try:
            # Upgrade pip first
            subprocess.run([str(python_path), "-m", "pip", "install", "--upgrade", "pip"], check=True)
            
            # Install requirements
            requirements_file = self.project_root / "requirements.txt"
            subprocess.run([str(pip_path), "install", "-r", str(requirements_file)], check=True)
            
            if dev_mode:
                # Install development dependencies
                dev_packages = [
                    "jupyter", "ipykernel", "notebook",
                    "pytest-xdist", "pytest-mock",
                    "pre-commit", "bandit", "safety"
                ]
                subprocess.run([str(pip_path), "install"] + dev_packages, check=True)
                print("✓ Development dependencies installed")
            
            print("✓ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install dependencies: {e}")
            return False
        return True
    
    def create_directories(self):
        """Create necessary directories."""
        print("Creating project directories...")
        
        directories = [
            "logs",
            "data/raw",
            "data/processed",
            "data/synthetic",
            "models/checkpoints",
            "models/trained",
            "outputs",
            "temp"
        ]
        
        for dir_path in directories:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ {dir_path}")
        
        print("✓ Directories created")
    
    def create_environment_file(self, env_type="development"):
        """Create .env file with environment variables."""
        print("Creating environment configuration...")
        
        env_content = f"""# Clinical NLQ AI Assistant Environment Configuration
# Environment: {env_type}

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=clinical_nlq
DB_USERNAME=nlq_user
DB_PASSWORD=your_secure_password_here
DB_SCHEMA=clinical_data

# Model Configuration
HUGGINGFACE_HUB_TOKEN=your_huggingface_token_here
MODEL_CACHE_DIR=./models/cache

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here
ENCRYPTION_KEY=your_encryption_key_here

# Optional: Voice Processing
AZURE_SPEECH_KEY=your_azure_speech_key_here
AZURE_SPEECH_REGION=eastus

# Optional: External Services
FHIR_AUTH_TOKEN=your_fhir_token_here

# Logging
LOG_LEVEL=INFO
AUDIT_ENABLED=true

# Development Settings
DEBUG={'true' if env_type == 'development' else 'false'}
ENVIRONMENT={env_type}
"""
        
        env_file = self.project_root / ".env"
        with open(env_file, "w") as f:
            f.write(env_content)
        
        print(f"✓ Environment file created at {env_file}")
        print("  ⚠️  Please update the .env file with your actual configuration values")
    
    def initialize_git(self):
        """Initialize git repository and create .gitignore."""
        print("Initializing Git repository...")
        
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# Environment Variables
.env
.env.*

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Jupyter Notebook
.ipynb_checkpoints

# Model Files
models/trained/
models/checkpoints/
models/cache/

# Data
data/raw/
data/processed/
!data/synthetic/

# Logs
logs/
*.log

# Temporary
temp/
tmp/
outputs/

# OS
.DS_Store
Thumbs.db

# Database
*.db
*.sqlite
*.sqlite3

# Security
*.pem
*.key
*.crt
"""
        
        gitignore_file = self.project_root / ".gitignore"
        with open(gitignore_file, "w") as f:
            f.write(gitignore_content)
        
        try:
            subprocess.run(["git", "init"], cwd=self.project_root, check=True)
            subprocess.run(["git", "add", ".gitignore"], cwd=self.project_root, check=True)
            print("✓ Git repository initialized")
        except subprocess.CalledProcessError:
            print("⚠️  Git not available or already initialized")
    
    def verify_installation(self):
        """Verify that the installation was successful."""
        print("Verifying installation...")
        
        # Check virtual environment
        if not self.venv_path.exists():
            print("✗ Virtual environment not found")
            return False
        
        # Check key files
        key_files = [
            "requirements.txt",
            "config/config.yaml",
            ".env",
            ".gitignore"
        ]
        
        for file_path in key_files:
            if not (self.project_root / file_path).exists():
                print(f"✗ {file_path} not found")
                return False
        
        print("✓ Installation verified successfully")
        return True
    
    def display_next_steps(self):
        """Display next steps for the user."""
        print("\n" + "="*60)
        print("🎉 Setup completed successfully!")
        print("="*60)
        print("\nNext steps:")
        print("\n1. Activate the virtual environment:")
        if os.name == 'nt':  # Windows
            print(f"   .\\venv\\Scripts\\activate")
        else:  # Unix/Linux/macOS
            print(f"   source venv/bin/activate")
        
        print("\n2. Update the .env file with your configuration:")
        print("   - Database connection details")
        print("   - API keys and tokens")
        print("   - Security keys")
        
        print("\n3. Set up PostgreSQL database:")
        print("   - Install PostgreSQL if not already installed")
        print("   - Create database and user")
        print("   - Run database migrations")
        
        print("\n4. Download or prepare clinical training data:")
        print("   - Place training data in data/raw/")
        print("   - Run data preprocessing scripts")
        
        print("\n5. Start development:")
        print("   streamlit run src/ui/main.py")
        
        print("\n6. Run tests:")
        print("   pytest tests/")
        
        print("\nFor more information, see:")
        print("- docs/phase1_problem_definition.md")
        print("- docs/phase1_requirements.md")
        print("- README.md")
        print("\n" + "="*60)


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="Setup Clinical NLQ AI Assistant")
    parser.add_argument("--dev", action="store_true", help="Development setup")
    parser.add_argument("--prod", action="store_true", help="Production setup")
    parser.add_argument("--test", action="store_true", help="Test environment setup")
    parser.add_argument("--skip-venv", action="store_true", help="Skip virtual environment creation")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency installation")
    
    args = parser.parse_args()
    
    # Determine environment type
    if args.prod:
        env_type = "production"
    elif args.test:
        env_type = "testing"
    else:
        env_type = "development"
    
    print(f"Setting up Clinical NLQ AI Assistant ({env_type} environment)")
    print("="*60)
    
    setup_manager = SetupManager()
    
    # Create virtual environment
    if not args.skip_venv:
        if not setup_manager.create_virtual_environment():
            sys.exit(1)
    
    # Install dependencies
    if not args.skip_deps:
        if not setup_manager.install_dependencies(dev_mode=args.dev or env_type == "development"):
            sys.exit(1)
    
    # Create directories
    setup_manager.create_directories()
    
    # Create environment file
    setup_manager.create_environment_file(env_type)
    
    # Initialize Git
    setup_manager.initialize_git()
    
    # Verify installation
    if not setup_manager.verify_installation():
        sys.exit(1)
    
    # Display next steps
    setup_manager.display_next_steps()


if __name__ == "__main__":
    main()