#!/usr/bin/env python3
"""
Test SQL detection functionality
"""

import sys
import os
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / 'src')
sys.path.insert(0, src_path)

def test_sql_detection():
    """Test the SQL detection logic"""
    
    # Mock the _is_sql_query method from streamlit app
    def _is_sql_query(text: str) -> bool:
        """
        Detect if the input text is SQL rather than natural language.
        """
        text_upper = text.upper().strip()
        
        # Common SQL keywords that indicate SQL rather than natural language
        sql_indicators = [
            'SELECT ',
            'INSERT ',
            'UPDATE ',
            'DELETE ',
            'CREATE ',
            'DROP ',
            'ALTER ',
            'TRUNCATE ',
            'WITH '
        ]
        
        # Check if text starts with SQL keywords
        for indicator in sql_indicators:
            if text_upper.startswith(indicator):
                return True
        
        # Additional checks for SQL patterns
        if ('FROM ' in text_upper and 
            ('SELECT' in text_upper or 'COUNT(' in text_upper or 'SUM(' in text_upper)):
            return True
        
        # Check for common SQL patterns
        sql_patterns = [
            'COUNT(*)',
            'COUNT(1)',
            'GROUP BY',
            'ORDER BY',
            'WHERE ',
            'HAVING ',
            'INNER JOIN',
            'LEFT JOIN',
            'RIGHT JOIN'
        ]
        
        for pattern in sql_patterns:
            if pattern in text_upper:
                return True
        
        return False
    
    # Test cases
    test_cases = [
        # SQL queries (should return True)
        ("SELECT COUNT(*) FROM clinical_data.patients", True),
        ("SELECT * FROM patients WHERE age > 65", True),
        ("select count(*) from conditions", True),
        ("INSERT INTO patients VALUES (...)", True),
        ("UPDATE patients SET name = 'John'", True),
        ("DELETE FROM patients WHERE id = 1", True),
        ("CREATE TABLE test (id INT)", True),
        ("COUNT(*) FROM patients", True),
        ("SELECT name, age FROM patients ORDER BY age", True),
        
        # Natural language queries (should return False)
        ("How many patients do we have?", False),
        ("Show me all male patients", False),
        ("Find patients with diabetes", False),
        ("What are the most common conditions?", False),
        ("List all providers", False),
        ("Which medications are prescribed most often?", False),
        ("Show patients over 65 years old", False),
        ("Count the number of encounters", False),
        ("Display patient demographics", False),
    ]
    
    print("🧪 Testing SQL Detection Logic")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for query, expected in test_cases:
        result = _is_sql_query(query)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        print(f"{status} | Expected: {expected} | Got: {result} | Query: '{query}'")
        
        if result == expected:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! SQL detection is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Review the logic above.")
        return False

if __name__ == "__main__":
    test_sql_detection()