#!/usr/bin/env python3
"""
Test script to debug the fallback SQL generator
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from nlq.fallback_sql_generator import FallbackSQLGenerator

def test_fallback_generator():
    """Test the fallback generator with the problematic query"""
    print("🧪 Testing Fallback SQL Generator...")
    
    generator = FallbackSQLGenerator()
    
    # Test the problematic query
    test_queries = [
        "How many patients received an HPV vaccine?",
        "How many patients",
        "How many patients are there?",
        "Show all patients"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        result = generator.generate_sql(query)
        
        print(f"📊 Generated SQL: {result['generated_sql']}")
        print(f"🔧 Method: {result['method']}")
        print(f"📋 Pattern matched: {result['pattern_matched']}")
        print(f"✅ Valid: {result['validation']['is_valid']}")
        if result['validation'].get('errors'):
            print(f"❌ Errors: {result['validation']['errors']}")
        if result['validation'].get('warnings'):
            print(f"⚠️ Warnings: {result['validation']['warnings']}")

if __name__ == "__main__":
    test_fallback_generator()