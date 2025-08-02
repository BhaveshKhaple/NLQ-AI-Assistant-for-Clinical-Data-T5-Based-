#!/usr/bin/env python3
"""
Fallback SQL Generator
Provides rule-based SQL generation for common queries when the T5 model fails.
"""

import re
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class FallbackSQLGenerator:
    """
    Rule-based SQL generator for common clinical queries.
    Used as fallback when T5 model generates invalid SQL.
    """
    
    def __init__(self):
        """Initialize the fallback generator with common patterns."""
        self.patterns = self._build_patterns()
        self.table_mappings = {
            'patient': 'clinical_data.patients',
            'patients': 'clinical_data.patients',
            'condition': 'clinical_data.conditions',
            'conditions': 'clinical_data.conditions',
            'medication': 'clinical_data.medications',
            'medications': 'clinical_data.medications',
            'encounter': 'clinical_data.encounters',
            'encounters': 'clinical_data.encounters',
            'provider': 'clinical_data.providers',
            'providers': 'clinical_data.providers',
            'organization': 'clinical_data.organizations',
            'organizations': 'clinical_data.organizations'
        }
    
    def _build_patterns(self) -> List[Dict[str, Any]]:
        """Build regex patterns for common query types."""
        return [
            # Vaccine-related queries (more specific, should come first)
            {
                'pattern': r'how many patients?.*(vaccine|vaccination|immuniz)',
                'template': 'SELECT COUNT(DISTINCT p.id) as total FROM clinical_data.patients p JOIN clinical_data.immunizations i ON p.id::text = i.patient WHERE i.description ILIKE \'%{vaccine_type}%\'',
                'extract_vaccine': True
            },
            # Condition count queries
            {
                'pattern': r'how many patients?.*(diagnosed with|have)\s+([a-zA-Z\s]+)',
                'template': 'SELECT COUNT(DISTINCT patient) as total FROM clinical_data.conditions WHERE description ILIKE \'%{condition}%\'',
                'extract_condition': True
            },
            # Top N queries
            {
                'pattern': r'top\s+(\d+).*most (common|frequent).*(conditions?|diagnoses)',
                'template': 'SELECT description, COUNT(*) AS frequency FROM clinical_data.conditions GROUP BY description ORDER BY frequency DESC LIMIT {limit}',
                'extract_limit': True
            },
            {
                'pattern': r'top\s+(\d+).*most (common|frequent).*(medications?|drugs?)',
                'template': 'SELECT description, COUNT(*) AS frequency FROM clinical_data.medications GROUP BY description ORDER BY frequency DESC LIMIT {limit}',
                'extract_limit': True
            },
            {
                'pattern': r'top\s+(\d+).*most (common|frequent).*(vaccines?|immunizations?)',
                'template': 'SELECT description, COUNT(*) AS frequency FROM clinical_data.immunizations GROUP BY description ORDER BY frequency DESC LIMIT {limit}',
                'extract_limit': True
            },
            # Year-based queries
            {
                'pattern': r'(list|show).*(all )?medications?.*(prescribed|given).*in\s+(\d{4})',
                'template': 'SELECT * FROM clinical_data.medications WHERE EXTRACT(YEAR FROM CAST(start AS DATE)) = {year}',
                'extract_year': True
            },
            {
                'pattern': r'how many procedures?.*(done|performed).*in\s+(\d{4})',
                'template': 'SELECT COUNT(*) as total FROM clinical_data.procedures WHERE EXTRACT(YEAR FROM CAST(date AS DATE)) = {year}',
                'extract_year': True
            },
            # Complex aggregation
            {
                'pattern': r'how many patients?.*(received|got|had).*more than\s+(\d+).*(immunizations?|vaccines?)',
                'template': 'SELECT COUNT(*) as total FROM (SELECT patient FROM clinical_data.immunizations GROUP BY patient HAVING COUNT(*) > {threshold}) AS patient_counts',
                'extract_threshold': True
            },
            # List distinct vaccines
            {
                'pattern': r'(list|show).*(all )?(distinct )?vaccines?',
                'template': 'SELECT DISTINCT description FROM clinical_data.immunizations ORDER BY description'
            },
            # Count queries (general pattern)
            {
                'pattern': r'how many (patients?|conditions?|medications?|encounters?)',
                'template': 'SELECT COUNT(*) as total FROM clinical_data.{table}',
                'table_map': {
                    'patient': 'patients', 'patients': 'patients',
                    'condition': 'conditions', 'conditions': 'conditions',
                    'medication': 'medications', 'medications': 'medications',
                    'encounter': 'encounters', 'encounters': 'encounters'
                }
            },
            # List all queries
            {
                'pattern': r'(show|list|get) (all )?patients?',
                'template': 'SELECT id, first_name, last_name, birth_date, gender FROM clinical_data.patients ORDER BY last_name LIMIT 100',
                'static': True
            },
            {
                'pattern': r'(show|list|get) (all )?conditions?',
                'template': 'SELECT DISTINCT description, COUNT(*) as frequency FROM clinical_data.conditions GROUP BY description ORDER BY frequency DESC LIMIT 50',
                'static': True
            },
            {
                'pattern': r'(show|list|get) (all )?medications?',
                'template': 'SELECT DISTINCT description, COUNT(*) as frequency FROM clinical_data.medications GROUP BY description ORDER BY frequency DESC LIMIT 50',
                'static': True
            },
            # Most common queries
            {
                'pattern': r'most common (conditions?|medications?|procedures?)',
                'template': 'SELECT description, COUNT(*) as frequency FROM clinical_data.{table} GROUP BY description ORDER BY frequency DESC LIMIT 20',
                'table_map': {
                    'condition': 'conditions', 'conditions': 'conditions',
                    'medication': 'medications', 'medications': 'medications',
                    'procedure': 'procedures', 'procedures': 'procedures'
                }
            },
            # High-cost patients
            {
                'pattern': r'high.?cost patients?.*?\$?(\d+)',
                'template': 'SELECT first_name, last_name, healthcare_expenses FROM clinical_data.patients WHERE healthcare_expenses > {amount} ORDER BY healthcare_expenses DESC LIMIT 50',
                'extract_amount': True
            },
            # Patients with specific condition
            {
                'pattern': r'patients? with (.+?)(?:\s|$)',
                'template': 'SELECT DISTINCT p.first_name, p.last_name, c.start_date FROM clinical_data.patients p JOIN clinical_data.encounters e ON p.id = e.patient_id JOIN clinical_data.conditions c ON e.id = c.encounter_id WHERE c.description ILIKE \'%{condition}%\' ORDER BY p.last_name LIMIT 100',
                'extract_condition': True
            },
            # Show specific condition diagnoses
            {
                'pattern': r'show (.+?) diagnoses',
                'template': 'SELECT p.first_name, p.last_name, c.start_date, pr.name as provider FROM clinical_data.patients p JOIN clinical_data.encounters e ON p.id = e.patient_id JOIN clinical_data.conditions c ON e.id = c.encounter_id JOIN clinical_data.providers pr ON e.provider_id = pr.id WHERE c.description ILIKE \'%{condition}%\' ORDER BY c.start_date DESC LIMIT 100',
                'extract_condition': True
            },
            # Age-based queries
            {
                'pattern': r'patients? (over|under|above|below) (\d+)',
                'template': 'SELECT first_name, last_name, birth_date, EXTRACT(YEAR FROM AGE(birth_date)) as age FROM clinical_data.patients WHERE EXTRACT(YEAR FROM AGE(birth_date)) {operator} {age} ORDER BY birth_date LIMIT 100',
                'extract_age': True
            }
        ]
    
    def generate_sql(self, nlq: str) -> Dict[str, Any]:
        """
        Generate SQL using rule-based patterns.
        
        Args:
            nlq: Natural language query
            
        Returns:
            Dict containing generated SQL and metadata
        """
        nlq_lower = nlq.lower().strip()
        
        for pattern_info in self.patterns:
            pattern = pattern_info['pattern']
            match = re.search(pattern, nlq_lower)
            
            if match:
                try:
                    sql = self._build_sql_from_pattern(pattern_info, match, nlq_lower)
                    if sql:
                        return {
                            'generated_sql': sql,
                            'method': 'fallback_rule_based',
                            'pattern_matched': pattern,
                            'confidence': 0.8,
                            'validation': {'is_valid': True, 'errors': []},
                            'nlq': nlq
                        }
                except Exception as e:
                    logger.warning(f"Error applying pattern {pattern}: {e}")
                    continue
        
        # Default fallback for unmatched queries
        return self._generate_default_fallback(nlq)
    
    def _build_sql_from_pattern(self, pattern_info: Dict[str, Any], match: re.Match, nlq: str) -> Optional[str]:
        """Build SQL from matched pattern."""
        template = pattern_info['template']
        
        # Handle static templates
        if pattern_info.get('static'):
            return template
        
        # Handle table mapping
        if 'table_map' in pattern_info:
            table_key = match.group(1) if match.groups() else 'patients'
            table = pattern_info['table_map'].get(table_key, 'patients')
            return template.format(table=table)
        
        # Handle amount extraction
        if pattern_info.get('extract_amount'):
            amount = match.group(1) if match.groups() else '1000'
            return template.format(amount=amount)
        
        # Handle condition extraction
        if pattern_info.get('extract_condition'):
            condition = match.group(1).strip() if match.groups() else 'condition'
            # Clean up the condition text
            condition = re.sub(r'[^\w\s]', '', condition).strip()
            return template.format(condition=condition)
        
        # Handle age extraction
        if pattern_info.get('extract_age'):
            direction = match.group(1) if len(match.groups()) >= 1 else 'over'
            age = match.group(2) if len(match.groups()) >= 2 else '18'
            operator = '>' if direction in ['over', 'above'] else '<'
            return template.format(operator=operator, age=age)
        
        # Handle vaccine extraction
        if pattern_info.get('extract_vaccine'):
            # Extract vaccine type from the query
            vaccine_keywords = ['hpv', 'flu', 'covid', 'hepatitis', 'measles', 'polio', 'tetanus']
            vaccine_type = 'vaccine'  # default
            
            nlq_lower = nlq.lower()
            for keyword in vaccine_keywords:
                if keyword in nlq_lower:
                    vaccine_type = keyword
                    break
            
            return template.format(vaccine_type=vaccine_type)
        
        # Handle limit extraction (for top N queries)
        if pattern_info.get('extract_limit'):
            limit = match.group(1) if match.groups() else '5'
            return template.format(limit=limit)
        
        # Handle year extraction
        if pattern_info.get('extract_year'):
            year_match = re.search(r'(\d{4})', nlq)
            year = year_match.group(1) if year_match else '2023'
            return template.format(year=year)
        
        # Handle threshold extraction (for "more than X" queries)
        if pattern_info.get('extract_threshold'):
            threshold_match = re.search(r'more than\s+(\d+)', nlq)
            threshold = threshold_match.group(1) if threshold_match else '2'
            return template.format(threshold=threshold)
        
        return template
    
    def _generate_default_fallback(self, nlq: str) -> Dict[str, Any]:
        """Generate a default fallback query."""
        # For unrecognized queries, return a safe default
        default_sql = "SELECT 'Query not recognized. Please try: How many patients, Show all patients, Most common conditions' as message"
        
        return {
            'generated_sql': default_sql,
            'method': 'fallback_default',
            'pattern_matched': 'none',
            'confidence': 0.3,
            'validation': {'is_valid': True, 'errors': [], 'warnings': ['Query pattern not recognized']},
            'nlq': nlq
        }
    
    def get_supported_patterns(self) -> List[str]:
        """Get list of supported query patterns."""
        return [
            "How many patients/conditions/medications?",
            "How many patients received [vaccine type]?",
            "Show/List all patients/conditions/medications",
            "Most common conditions/medications/procedures",
            "High-cost patients over $X",
            "Patients with [condition name]",
            "Patients over/under [age]"
        ]