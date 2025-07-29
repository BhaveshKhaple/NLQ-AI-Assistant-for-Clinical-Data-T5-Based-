#!/usr/bin/env python3
"""
Environment variable loader utility
"""

import os
from pathlib import Path

def load_env_file(env_path: str = None):
    """
    Load environment variables from .env file
    
    Args:
        env_path: Path to .env file. If None, looks for .env in project root
    """
    if env_path is None:
        # Look for .env file in project root
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent  # Go up two levels from src/utils
        env_path = project_root / '.env'
    else:
        env_path = Path(env_path)
    
    if not env_path.exists():
        print(f"Warning: .env file not found at {env_path}")
        return
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse key=value pairs
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    # Set environment variable
                    os.environ[key] = value
                else:
                    print(f"Warning: Invalid line format at line {line_num}: {line}")
        
        print(f"✅ Environment variables loaded from {env_path}")
        
    except Exception as e:
        print(f"❌ Failed to load .env file: {e}")

def print_db_env_vars():
    """Print database-related environment variables for debugging"""
    db_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USERNAME', 'DB_PASSWORD', 'DB_SCHEMA']
    
    print("Database Environment Variables:")
    for var in db_vars:
        value = os.getenv(var, 'NOT SET')
        if var == 'DB_PASSWORD' and value != 'NOT SET':
            value = '*' * len(value)  # Hide password
        print(f"  {var}: {value}")

if __name__ == "__main__":
    load_env_file()
    print_db_env_vars()