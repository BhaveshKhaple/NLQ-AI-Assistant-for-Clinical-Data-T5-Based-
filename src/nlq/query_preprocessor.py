#!/usr/bin/env python3
"""
Query Preprocessor
Maps user queries to formats that the trained T5 model can better understand.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class QueryMapping:
    """Represents a query transformation mapping"""
    pattern: str
    template: str
    variables: Dict[str, str]
    confidence: float

class QueryPreprocessor:
    """
    Preprocesses natural language queries to match training data patterns.
    """
    
    def __init__(self):
        """Initialize the query preprocessor with mapping rules."""
        self.mappings = self._build_mappings()
        self.medical_terms = self._build_medical_terms()
        
    def _build_mappings(self) -> List[QueryMapping]:
        """Build query mapping rules based on training data patterns."""
        return [
            # Most specific patterns first - patients with more than X immunizations
            QueryMapping(
                pattern=r'how many patients?.*(received|got|had).*more than\s+(\d+).*(immunizations?|vaccines?)',
                template='How many patients received more than {number} immunizations?',
                variables={'number': ''},
                confidence=0.95
            ),
            # Vaccine/Immunization queries (general)
            QueryMapping(
                pattern=r'how many patients?.*(received|got|had).*(vaccine|vaccination|immuniz|shot)',
                template='How many patients have received {vaccine_type}?',
                variables={'vaccine_type': 'vaccination'},
                confidence=0.9
            ),
            QueryMapping(
                pattern=r'how many patients?.*(hpv|human papillomavirus)',
                template='How many patients have received HPV vaccination?',
                variables={'vaccine_type': 'HPV'},
                confidence=0.95
            ),
            QueryMapping(
                pattern=r'how many patients?.*(flu|influenza)',
                template='How many patients have received flu vaccination?',
                variables={'vaccine_type': 'influenza'},
                confidence=0.95
            ),
            QueryMapping(
                pattern=r'how many patients?.*(covid|coronavirus)',
                template='How many patients have received COVID vaccination?',
                variables={'vaccine_type': 'COVID'},
                confidence=0.95
            ),
            
            # Medication queries
            QueryMapping(
                pattern=r'how many patients?.*(taking|prescribed|on).*(medication|medicine|drug)',
                template='How many patients are taking {medication}?',
                variables={'medication': 'medication'},
                confidence=0.85
            ),
            
            # Condition/Disease queries
            QueryMapping(
                pattern=r'how many patients?.*(have|diagnosed with|suffering from).*(condition|disease|illness)',
                template='How many patients have been diagnosed with {condition}?',
                variables={'condition': 'condition'},
                confidence=0.85
            ),
            
            # Age-based queries
            QueryMapping(
                pattern=r'how many patients?.*(over|above|older than|greater than)\s*(\d+)',
                template='How many patients are over {age} years old?',
                variables={'age': ''},
                confidence=0.9
            ),
            QueryMapping(
                pattern=r'how many patients?.*(under|below|younger than|less than)\s*(\d+)',
                template='How many patients are under {age} years old?',
                variables={'age': ''},
                confidence=0.9
            ),
            
            # Gender-based queries
            QueryMapping(
                pattern=r'how many (male|female|men|women) patients?',
                template='How many {gender} patients are there?',
                variables={'gender': ''},
                confidence=0.9
            ),
            
            # Location-based queries
            QueryMapping(
                pattern=r'how many patients?.*(from|in|living in)\s*([A-Z]{2}|[A-Za-z\s]+)',
                template='How many patients are from {location}?',
                variables={'location': ''},
                confidence=0.85
            ),
            
            # General count queries
            QueryMapping(
                pattern=r'how many patients?(?!\s+.*\b(?:received|got|had|taking|prescribed|have|diagnosed|over|under|from|in)\b)',
                template='How many patients are in the database?',
                variables={},
                confidence=0.8
            ),
            
            # Provider/Organization queries
            QueryMapping(
                pattern=r'how many (providers?|doctors?|physicians?)',
                template='How many providers are there?',
                variables={},
                confidence=0.9
            ),
            QueryMapping(
                pattern=r'how many (organizations?|hospitals?|clinics?)',
                template='How many organizations are there?',
                variables={},
                confidence=0.9
            ),
            
            # Show/List queries
            QueryMapping(
                pattern=r'(show|list|display).*(all )?patients?',
                template='Show me all patients',
                variables={},
                confidence=0.85
            ),
            QueryMapping(
                pattern=r'(show|list|display).*(all )?(conditions?|diagnoses)',
                template='Show me all medical conditions',
                variables={},
                confidence=0.85
            ),
            QueryMapping(
                pattern=r'(show|list|display).*(all )?(medications?|drugs?)',
                template='Show me all medications',
                variables={},
                confidence=0.85
            ),
            
            # New patterns based on provided examples
            QueryMapping(
                pattern=r'how many patients?.*(diagnosed with|have)\s+([a-zA-Z\s]+)',
                template='How many patients were diagnosed with {condition}?',
                variables={'condition': ''},
                confidence=0.9
            ),
            QueryMapping(
                pattern=r'(list|show).*(all )?medications?.*(prescribed|given).*in\s+(\d{4})',
                template='List all medications prescribed in {year}',
                variables={'year': ''},
                confidence=0.9
            ),
            QueryMapping(
                pattern=r'how many procedures?.*(done|performed).*in\s+(\d{4})',
                template='How many procedures were done in {year}?',
                variables={'year': ''},
                confidence=0.9
            ),
            QueryMapping(
                pattern=r'top\s+(\d+).*most (common|frequent).*(conditions?|diagnoses)',
                template='Top {number} most common conditions',
                variables={'number': ''},
                confidence=0.95
            ),
            QueryMapping(
                pattern=r'most (common|frequent).*(conditions?|diagnoses)',
                template='Most common conditions',
                variables={},
                confidence=0.9
            ),
            QueryMapping(
                pattern=r'top\s+(\d+).*most (common|frequent).*(medications?|drugs?)',
                template='Top {number} most common medications',
                variables={'number': ''},
                confidence=0.95
            ),
            QueryMapping(
                pattern=r'most (common|frequent).*(medications?|drugs?)',
                template='Most common medications',
                variables={},
                confidence=0.9
            ),
            QueryMapping(
                pattern=r'top\s+(\d+).*most (common|frequent).*(vaccines?|immunizations?)',
                template='Top {number} most frequent vaccines',
                variables={'number': ''},
                confidence=0.95
            ),
            QueryMapping(
                pattern=r'most (common|frequent).*(vaccines?|immunizations?)',
                template='Most frequent vaccines',
                variables={},
                confidence=0.9
            ),
            QueryMapping(
                pattern=r'(list|show).*(all )?(distinct )?vaccines?',
                template='List all distinct vaccines',
                variables={},
                confidence=0.9
            ),
            QueryMapping(
                pattern=r'(list|show).*(all )?procedures?.*(involving|with|for)\s+([a-zA-Z\s]+)',
                template='List all procedures involving {condition}',
                variables={'condition': ''},
                confidence=0.9
            ),
            QueryMapping(
                pattern=r'(list|show).*(all )?procedures?.*(not involving|without)\s+([a-zA-Z\s]+)',
                template='List all procedures not involving {condition}',
                variables={'condition': ''},
                confidence=0.9
            ),
            QueryMapping(
                pattern=r'(which|what) payers?.*(covered|have).*more than\s+(\d+)',
                template='Which payers covered more than {number} patients?',
                variables={'number': ''},
                confidence=0.9
            ),

        ]
    
    def _build_medical_terms(self) -> Dict[str, List[str]]:
        """Build medical term mappings for normalization."""
        return {
            'vaccines': [
                'hpv', 'human papillomavirus', 'flu', 'influenza', 'covid', 'coronavirus',
                'hepatitis', 'measles', 'mumps', 'rubella', 'polio', 'tetanus', 'diphtheria'
            ],
            'conditions': [
                'diabetes', 'hypertension', 'high blood pressure', 'depression', 'anxiety',
                'asthma', 'copd', 'heart disease', 'cancer', 'stroke', 'arthritis'
            ],
            'medications': [
                'insulin', 'metformin', 'lisinopril', 'atorvastatin', 'aspirin', 'ibuprofen',
                'acetaminophen', 'hydrocodone', 'oxycodone', 'prednisone'
            ]
        }
    
    def preprocess_query(self, nlq: str) -> Dict[str, any]:
        """
        Preprocess a natural language query to match training patterns.
        
        Args:
            nlq: Original natural language query
            
        Returns:
            Dict containing preprocessed query and metadata
        """
        original_query = nlq.strip()
        normalized_query = self._normalize_query(original_query)
        
        # Try to find a matching pattern
        best_mapping = None
        best_match = None
        highest_confidence = 0.0
        
        for mapping in self.mappings:
            match = re.search(mapping.pattern, normalized_query, re.IGNORECASE)
            if match and mapping.confidence > highest_confidence:
                best_mapping = mapping
                best_match = match
                highest_confidence = mapping.confidence
        
        if best_mapping:
            # Extract variables from the match
            extracted_vars = self._extract_variables(best_match, best_mapping, normalized_query)
            
            # Generate the preprocessed query
            preprocessed_query = self._apply_mapping(best_mapping, extracted_vars)
            
            return {
                'original_query': original_query,
                'preprocessed_query': preprocessed_query,
                'mapping_applied': True,
                'mapping_pattern': best_mapping.pattern,
                'confidence': best_mapping.confidence,
                'extracted_variables': extracted_vars,
                'method': 'pattern_mapping'
            }
        else:
            # No mapping found, try semantic similarity or return original
            semantic_result = self._try_semantic_mapping(normalized_query)
            
            if semantic_result:
                return semantic_result
            else:
                return {
                    'original_query': original_query,
                    'preprocessed_query': original_query,  # No change
                    'mapping_applied': False,
                    'confidence': 0.5,
                    'method': 'no_mapping'
                }
    
    def _normalize_query(self, query: str) -> str:
        """Normalize the query for better pattern matching."""
        # Convert to lowercase
        normalized = query.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Normalize common variations
        replacements = {
            r'\bhow many\b': 'how many',
            r'\bshow me\b': 'show',
            r'\blist all\b': 'list',
            r'\bdisplay all\b': 'show',
            r'\bget all\b': 'show',
            r'\bfind all\b': 'show',
            r'\bpatients?\b': 'patients',
            r'\bpeople\b': 'patients',
            r'\bindividuals?\b': 'patients',
        }
        
        for pattern, replacement in replacements.items():
            normalized = re.sub(pattern, replacement, normalized)
        
        return normalized
    
    def _extract_variables(self, match: re.Match, mapping: QueryMapping, query: str) -> Dict[str, str]:
        """Extract variables from the matched pattern."""
        variables = {}
        
        # Extract age from age-based queries
        if 'age' in mapping.variables:
            age_match = re.search(r'(\d+)', query)
            if age_match:
                variables['age'] = age_match.group(1)
        
        # Extract gender
        if 'gender' in mapping.variables:
            gender_match = re.search(r'\b(male|female|men|women)\b', query, re.IGNORECASE)
            if gender_match:
                gender = gender_match.group(1).lower()
                if gender in ['men', 'male']:
                    variables['gender'] = 'male'
                elif gender in ['women', 'female']:
                    variables['gender'] = 'female'
        
        # Extract location
        if 'location' in mapping.variables:
            location_match = re.search(r'(?:from|in|living in)\s+([A-Z]{2}|[A-Za-z\s]+)', query, re.IGNORECASE)
            if location_match:
                variables['location'] = location_match.group(1).strip()
        
        # Extract specific medical terms
        if 'vaccine_type' in mapping.variables:
            for vaccine in self.medical_terms['vaccines']:
                if vaccine in query.lower():
                    variables['vaccine_type'] = vaccine
                    break
        
        if 'condition' in mapping.variables:
            # Try to extract from pattern match first
            condition_match = re.search(r'(?:diagnosed with|have|with|involving|for)\s+([a-zA-Z\s]+?)(?:\s|$|[?.])', query, re.IGNORECASE)
            if condition_match:
                variables['condition'] = condition_match.group(1).strip()
            else:
                # Fall back to predefined conditions
                for condition in self.medical_terms['conditions']:
                    if condition in query.lower():
                        variables['condition'] = condition
                        break
        
        if 'medication' in mapping.variables:
            for medication in self.medical_terms['medications']:
                if medication in query.lower():
                    variables['medication'] = medication
                    break
        
        # Extract year
        if 'year' in mapping.variables:
            year_match = re.search(r'(\d{4})', query)
            if year_match:
                variables['year'] = year_match.group(1)
        
        # Extract number/limit
        if 'number' in mapping.variables:
            number_match = re.search(r'(?:top|first)\s+(\d+)', query, re.IGNORECASE)
            if number_match:
                variables['number'] = number_match.group(1)
            else:
                # Look for "more than X"
                more_than_match = re.search(r'more than\s+(\d+)', query, re.IGNORECASE)
                if more_than_match:
                    variables['number'] = more_than_match.group(1)
        
        return variables
    
    def _apply_mapping(self, mapping: QueryMapping, variables: Dict[str, str]) -> str:
        """Apply the mapping template with extracted variables."""
        template = mapping.template
        
        # Replace variables in template
        for var_name, var_value in variables.items():
            if var_value:
                template = template.replace(f'{{{var_name}}}', var_value)
        
        # Clean up any remaining placeholders
        template = re.sub(r'\{[^}]+\}', '', template)
        template = re.sub(r'\s+', ' ', template).strip()
        
        return template
    
    def _try_semantic_mapping(self, query: str) -> Optional[Dict[str, any]]:
        """Try semantic similarity mapping for unmatched queries."""
        # This could be enhanced with embeddings or similarity matching
        # For now, we'll use simple keyword matching
        
        keywords_to_patterns = {
            'count': 'How many patients are in the database?',
            'total': 'How many patients are in the database?',
            'number': 'How many patients are in the database?',
            'patients': 'Show me all patients',
            'conditions': 'Show me all medical conditions',
            'medications': 'Show me all medications',
            'providers': 'How many providers are there?',
            'organizations': 'How many organizations are there?'
        }
        
        for keyword, pattern in keywords_to_patterns.items():
            if keyword in query.lower():
                return {
                    'original_query': query,
                    'preprocessed_query': pattern,
                    'mapping_applied': True,
                    'confidence': 0.6,
                    'method': 'semantic_mapping',
                    'matched_keyword': keyword
                }
        
        return None
    
    def get_supported_patterns(self) -> List[str]:
        """Get list of supported query patterns."""
        return [
            "How many patients received [vaccine type]?",
            "How many patients are taking [medication]?",
            "How many patients have [condition]?",
            "How many patients are over/under [age]?",
            "How many [gender] patients?",
            "How many patients from [location]?",
            "Show/List all patients/conditions/medications",
            "How many providers/organizations?"
        ]