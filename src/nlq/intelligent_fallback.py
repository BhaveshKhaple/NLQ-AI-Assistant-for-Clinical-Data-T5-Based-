#!/usr/bin/env python3
"""
Intelligent Fallback System
Combines rule-based patterns with query understanding for better SQL generation.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from .fallback_sql_generator import FallbackSQLGenerator

logger = logging.getLogger(__name__)

class IntelligentFallback:
    """
    Enhanced fallback system that understands query intent and generates appropriate SQL.
    """
    
    def __init__(self):
        """Initialize the intelligent fallback system."""
        self.basic_fallback = FallbackSQLGenerator()
        self.intent_patterns = self._build_intent_patterns()
        self.entity_extractors = self._build_entity_extractors()
        
    def _build_intent_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Build intent recognition patterns."""
        return {
            'count_patients': {
                'patterns': [
                    r'how many patients?',
                    r'count.*patients?',
                    r'number of patients?',
                    r'total patients?'
                ],
                'base_sql': 'SELECT COUNT(*) as total FROM clinical_data.patients',
                'filters': []
            },
            'count_patients_with_condition': {
                'patterns': [
                    r'how many patients?.*(have|with|diagnosed|suffering)',
                    r'patients?.*(diagnosed|condition|disease|illness)'
                ],
                'base_sql': 'SELECT COUNT(DISTINCT p.id) as total FROM clinical_data.patients p JOIN clinical_data.conditions c ON p.id = c.patient_id',
                'filters': ['condition']
            },
            'count_patients_with_medication': {
                'patterns': [
                    r'how many patients?.*(taking|prescribed|on|using).*(medication|medicine|drug)',
                    r'patients?.*(medication|medicine|drug|prescription)'
                ],
                'base_sql': 'SELECT COUNT(DISTINCT p.id) as total FROM clinical_data.patients p JOIN clinical_data.medications m ON p.id = m.patient_id',
                'filters': ['medication']
            },
            'count_patients_with_vaccine': {
                'patterns': [
                    r'how many patients?.*(received|got|had).*(vaccine|vaccination|immuniz|shot)',
                    r'patients?.*(vaccine|vaccination|immuniz|shot)'
                ],
                'base_sql': 'SELECT COUNT(DISTINCT p.id) as total FROM clinical_data.patients p JOIN clinical_data.immunizations i ON p.id::text = i.patient',
                'filters': ['vaccine']
            },
            'count_patients_by_age': {
                'patterns': [
                    r'how many patients?.*(over|under|above|below|older|younger).*(\d+)',
                    r'patients?.*(age|years old|aged)'
                ],
                'base_sql': 'SELECT COUNT(*) as total FROM clinical_data.patients',
                'filters': ['age']
            },
            'count_patients_by_gender': {
                'patterns': [
                    r'how many (male|female|men|women) patients?',
                    r'patients?.*(male|female|gender)'
                ],
                'base_sql': 'SELECT COUNT(*) as total FROM clinical_data.patients',
                'filters': ['gender']
            },
            'count_patients_by_location': {
                'patterns': [
                    r'how many patients?.*(from|in|living).*(state|city|location)',
                    r'patients?.*(state|city|location|from|in)'
                ],
                'base_sql': 'SELECT COUNT(*) as total FROM clinical_data.patients',
                'filters': ['location']
            },
            'list_patients': {
                'patterns': [
                    r'(show|list|display|get).*(all )?patients?',
                    r'patients?.*(list|show|display)'
                ],
                'base_sql': 'SELECT id, first_name, last_name, birth_date, gender FROM clinical_data.patients ORDER BY last_name',
                'filters': []
            },
            'list_conditions': {
                'patterns': [
                    r'(show|list|display).*(all )?(conditions?|diagnoses|diseases)',
                    r'(conditions?|diagnoses|diseases).*(list|show|display)'
                ],
                'base_sql': 'SELECT DISTINCT description, COUNT(*) as frequency FROM clinical_data.conditions GROUP BY description ORDER BY frequency DESC',
                'filters': []
            },
            'list_medications': {
                'patterns': [
                    r'(show|list|display).*(all )?(medications?|drugs?|medicines?)',
                    r'(medications?|drugs?|medicines?).*(list|show|display)'
                ],
                'base_sql': 'SELECT DISTINCT description, COUNT(*) as frequency FROM clinical_data.medications GROUP BY description ORDER BY frequency DESC',
                'filters': []
            },
            'count_providers': {
                'patterns': [
                    r'how many (providers?|doctors?|physicians?)',
                    r'count.*providers?'
                ],
                'base_sql': 'SELECT COUNT(*) as total FROM clinical_data.providers',
                'filters': []
            },
            'count_organizations': {
                'patterns': [
                    r'how many (organizations?|hospitals?|clinics?)',
                    r'count.*(organizations?|hospitals?|clinics?)'
                ],
                'base_sql': 'SELECT COUNT(*) as total FROM clinical_data.organizations',
                'filters': []
            },
            
            # New patterns based on the provided examples
            'count_patients_with_condition': {
                'patterns': [
                    r'how many patients?.*(diagnosed with|have|with)\s+([a-zA-Z\s]+)',
                    r'patients?.*(diagnosed with|have|with)\s+([a-zA-Z\s]+)'
                ],
                'base_sql': 'SELECT COUNT(DISTINCT patient) as total FROM clinical_data.conditions',
                'filters': ['condition']
            },
            'medications_by_year': {
                'patterns': [
                    r'(list|show).*(all )?medications?.*(prescribed|given).*in\s+(\d{4})',
                    r'medications?.*(prescribed|given).*in\s+(\d{4})'
                ],
                'base_sql': 'SELECT * FROM clinical_data.medications',
                'filters': ['year']
            },
            'procedures_by_year': {
                'patterns': [
                    r'how many procedures?.*(done|performed).*in\s+(\d{4})',
                    r'procedures?.*(done|performed).*in\s+(\d{4})'
                ],
                'base_sql': 'SELECT COUNT(*) as total FROM clinical_data.procedures',
                'filters': ['year']
            },
            'top_conditions': {
                'patterns': [
                    r'top\s+(\d+).*most (common|frequent).*(conditions?|diagnoses)',
                    r'most (common|frequent).*(conditions?|diagnoses)',
                    r'(common|frequent).*(conditions?|diagnoses)'
                ],
                'base_sql': 'SELECT description, COUNT(*) AS frequency FROM clinical_data.conditions GROUP BY description ORDER BY frequency DESC',
                'filters': ['limit']
            },
            'top_medications': {
                'patterns': [
                    r'top\s+(\d+).*most (common|frequent).*(medications?|drugs?)',
                    r'most (common|frequent).*(medications?|drugs?)',
                    r'(common|frequent).*(medications?|drugs?)'
                ],
                'base_sql': 'SELECT description, COUNT(*) AS frequency FROM clinical_data.medications GROUP BY description ORDER BY frequency DESC',
                'filters': ['limit']
            },
            'top_vaccines': {
                'patterns': [
                    r'top\s+(\d+).*most (common|frequent).*(vaccines?|immunizations?)',
                    r'most (common|frequent).*(vaccines?|immunizations?)',
                    r'(frequent|common).*(vaccines?|immunizations?)'
                ],
                'base_sql': 'SELECT description, COUNT(*) AS frequency FROM clinical_data.immunizations GROUP BY description ORDER BY frequency DESC',
                'filters': ['limit']
            },
            'list_distinct_vaccines': {
                'patterns': [
                    r'(list|show).*(all )?(distinct )?vaccines?',
                    r'(list|show).*(all )?(distinct )?immunizations?'
                ],
                'base_sql': 'SELECT DISTINCT description FROM clinical_data.immunizations ORDER BY description',
                'filters': []
            },
            'procedures_with_condition': {
                'patterns': [
                    r'(list|show).*(all )?procedures?.*(involving|with|for)\s+([a-zA-Z\s]+)',
                    r'procedures?.*(involving|with|for)\s+([a-zA-Z\s]+)'
                ],
                'base_sql': 'SELECT DISTINCT description FROM clinical_data.procedures',
                'filters': ['condition_filter']
            },
            'procedures_without_condition': {
                'patterns': [
                    r'(list|show).*(all )?procedures?.*(not involving|without|not for)\s+([a-zA-Z\s]+)',
                    r'procedures?.*(not involving|without|not for)\s+([a-zA-Z\s]+)'
                ],
                'base_sql': 'SELECT DISTINCT description FROM clinical_data.procedures',
                'filters': ['condition_filter_not']
            },
            'payers_with_threshold': {
                'patterns': [
                    r'(which|what) payers?.*(covered|have).*more than\s+(\d+)',
                    r'payers?.*(covered|have).*more than\s+(\d+)'
                ],
                'base_sql': 'SELECT name FROM clinical_data.payers',
                'filters': ['threshold']
            },
            'patients_with_multiple_immunizations': {
                'patterns': [
                    r'how many patients?.*(received|got|had).*more than\s+(\d+).*(immunizations?|vaccines?)',
                    r'patients?.*(received|got|had).*more than\s+(\d+).*(immunizations?|vaccines?)'
                ],
                'base_sql': 'SELECT COUNT(*) as total FROM (SELECT patient FROM clinical_data.immunizations GROUP BY patient HAVING COUNT(*) > {threshold}) AS patient_counts',
                'filters': ['threshold']
            }
        }
    
    def _build_entity_extractors(self) -> Dict[str, Dict[str, Any]]:
        """Build entity extraction patterns."""
        return {
            'condition': {
                'patterns': [
                    r'(?:with|have|diagnosed|suffering from)\s+([a-zA-Z\s]+?)(?:\s|$|[?.])',
                    r'(?:condition|disease|illness)\s+([a-zA-Z\s]+?)(?:\s|$|[?.])',
                    r'([a-zA-Z\s]+?)\s+(?:condition|disease|diagnosis)'
                ],
                'filter_template': "WHERE c.description ILIKE '%{value}%'"
            },
            'medication': {
                'patterns': [
                    r'(?:taking|prescribed|on|using)\s+([a-zA-Z\s]+?)(?:\s|$|[?.])',
                    r'(?:medication|medicine|drug)\s+([a-zA-Z\s]+?)(?:\s|$|[?.])',
                    r'([a-zA-Z\s]+?)\s+(?:medication|medicine|drug)'
                ],
                'filter_template': "WHERE m.description ILIKE '%{value}%'"
            },
            'vaccine': {
                'patterns': [
                    r'(?:received|got|had)\s+(?:an?\s+)?([a-zA-Z\s]+?)\s+(?:vaccine|vaccination|immuniz|shot)',
                    r'([a-zA-Z\s]+?)\s+(?:vaccine|vaccination|immuniz|shot)',
                    r'(?:vaccine|vaccination|immuniz|shot)\s+(?:for|against)\s+([a-zA-Z\s]+?)'
                ],
                'filter_template': "WHERE i.description ILIKE '%{value}%'"
            },
            'age': {
                'patterns': [
                    r'(?:over|above|older than|greater than)\s+(\d+)',
                    r'(?:under|below|younger than|less than)\s+(\d+)',
                    r'aged?\s+(\d+)',
                    r'(\d+)\s+years?\s+old'
                ],
                'filter_template': "WHERE EXTRACT(YEAR FROM AGE(birth_date)) {operator} {value}"
            },
            'gender': {
                'patterns': [
                    r'\b(male|female|men|women)\b'
                ],
                'filter_template': "WHERE gender = '{value}'"
            },
            'location': {
                'patterns': [
                    r'(?:from|in|living in)\s+([A-Z]{2}|[A-Za-z\s]+?)(?:\s|$|[?.])',
                    r'(?:state|city)\s+([A-Za-z\s]+?)(?:\s|$|[?.])'
                ],
                'filter_template': "WHERE (state ILIKE '%{value}%' OR city ILIKE '%{value}%')"
            },
            'year': {
                'patterns': [
                    r'in\s+(\d{4})',
                    r'during\s+(\d{4})',
                    r'(\d{4})'
                ],
                'filter_template': "WHERE EXTRACT(YEAR FROM CAST(start AS DATE)) = {value}"
            },
            'limit': {
                'patterns': [
                    r'top\s+(\d+)',
                    r'first\s+(\d+)',
                    r'(\d+)\s+most'
                ],
                'filter_template': "LIMIT {value}"
            },
            'threshold': {
                'patterns': [
                    r'more than\s+(\d+)',
                    r'greater than\s+(\d+)',
                    r'over\s+(\d+)'
                ],
                'filter_template': ""  # Handled specially in SQL building
            },
            'condition_filter': {
                'patterns': [
                    r'(?:involving|with|for)\s+([a-zA-Z\s]+?)(?:\s|$|[?.])',
                    r'(?:related to|about)\s+([a-zA-Z\s]+?)(?:\s|$|[?.])'
                ],
                'filter_template': "WHERE description ILIKE '%{value}%'"
            },
            'condition_filter_not': {
                'patterns': [
                    r'(?:not involving|without|not for)\s+([a-zA-Z\s]+?)(?:\s|$|[?.])',
                    r'(?:not related to|not about)\s+([a-zA-Z\s]+?)(?:\s|$|[?.])'
                ],
                'filter_template': "WHERE description NOT ILIKE '%{value}%'"
            }
        }
    
    def generate_sql(self, nlq: str) -> Dict[str, Any]:
        """
        Generate SQL using intelligent fallback with intent recognition.
        
        Args:
            nlq: Natural language query
            
        Returns:
            Dict containing generated SQL and metadata
        """
        nlq_lower = nlq.lower().strip()
        
        # Step 1: Try to identify intent
        intent, confidence = self._identify_intent(nlq_lower)
        
        if intent and confidence > 0.7:
            # Step 2: Extract entities based on intent
            entities = self._extract_entities(nlq_lower, intent)
            
            # Step 3: Build SQL based on intent and entities
            sql = self._build_sql_from_intent(intent, entities, nlq_lower)
            
            if sql:
                return {
                    'generated_sql': sql,
                    'method': 'intelligent_fallback',
                    'intent': intent,
                    'entities': entities,
                    'confidence': confidence,
                    'validation': {'is_valid': True, 'errors': []},
                    'nlq': nlq
                }
        
        # Step 4: Fall back to basic rule-based generator
        logger.info(f"🔄 Using basic fallback for query: {nlq}")
        return self.basic_fallback.generate_sql(nlq)
    
    def _identify_intent(self, nlq: str) -> Tuple[Optional[str], float]:
        """Identify the intent of the query."""
        best_intent = None
        best_score = 0.0
        
        for intent_name, intent_data in self.intent_patterns.items():
            for pattern in intent_data['patterns']:
                if re.search(pattern, nlq, re.IGNORECASE):
                    # Calculate confidence based on pattern specificity
                    confidence = self._calculate_pattern_confidence(pattern, nlq)
                    if confidence > best_score:
                        best_intent = intent_name
                        best_score = confidence
        
        return best_intent, best_score
    
    def _calculate_pattern_confidence(self, pattern: str, nlq: str) -> float:
        """Calculate confidence score for a pattern match."""
        # More specific patterns get higher confidence
        base_confidence = 0.8
        
        # Boost confidence for exact matches
        if len(re.findall(r'\w+', pattern)) == len(re.findall(r'\w+', nlq)):
            base_confidence += 0.1
        
        # Boost confidence for specific medical terms
        medical_terms = ['vaccine', 'medication', 'condition', 'diagnosis', 'treatment']
        for term in medical_terms:
            if term in pattern.lower() and term in nlq.lower():
                base_confidence += 0.05
        
        return min(base_confidence, 1.0)
    
    def _extract_entities(self, nlq: str, intent: str) -> Dict[str, str]:
        """Extract entities based on the identified intent."""
        entities = {}
        
        # Get required filters for this intent
        intent_data = self.intent_patterns.get(intent, {})
        required_filters = intent_data.get('filters', [])
        
        for filter_type in required_filters:
            if filter_type in self.entity_extractors:
                extractor = self.entity_extractors[filter_type]
                
                for pattern in extractor['patterns']:
                    match = re.search(pattern, nlq, re.IGNORECASE)
                    if match:
                        value = match.group(1).strip()
                        
                        # Clean and normalize the extracted value
                        value = self._normalize_entity_value(filter_type, value)
                        
                        if value:
                            entities[filter_type] = value
                            break
        
        return entities
    
    def _normalize_entity_value(self, entity_type: str, value: str) -> str:
        """Normalize extracted entity values."""
        value = value.strip()
        
        if entity_type == 'gender':
            if value.lower() in ['men', 'male']:
                return 'M'
            elif value.lower() in ['women', 'female']:
                return 'F'
        
        elif entity_type == 'vaccine':
            # Normalize vaccine names
            vaccine_mappings = {
                'hpv': 'HPV',
                'human papillomavirus': 'HPV',
                'flu': 'influenza',
                'covid': 'COVID',
                'coronavirus': 'COVID'
            }
            return vaccine_mappings.get(value.lower(), value)
        
        elif entity_type == 'condition':
            # Clean up condition names
            value = re.sub(r'[^\w\s]', '', value).strip()
            return value
        
        elif entity_type == 'medication':
            # Clean up medication names
            value = re.sub(r'[^\w\s]', '', value).strip()
            return value
        
        return value
    
    def _build_sql_from_intent(self, intent: str, entities: Dict[str, str], nlq: str) -> Optional[str]:
        """Build SQL query from intent and extracted entities."""
        intent_data = self.intent_patterns.get(intent)
        if not intent_data:
            return None
        
        base_sql = intent_data['base_sql']
        required_filters = intent_data.get('filters', [])
        
        # Build WHERE clauses and other SQL modifications
        where_clauses = []
        sql_modifications = []
        
        for filter_type in required_filters:
            if filter_type in entities and filter_type in self.entity_extractors:
                extractor = self.entity_extractors[filter_type]
                filter_template = extractor['filter_template']
                
                if filter_type == 'age':
                    # Special handling for age filters
                    age_value = entities[filter_type]
                    if 'over' in nlq or 'above' in nlq or 'older' in nlq:
                        operator = '>'
                    elif 'under' in nlq or 'below' in nlq or 'younger' in nlq:
                        operator = '<'
                    else:
                        operator = '='
                    
                    where_clause = filter_template.format(operator=operator, value=age_value)
                    where_clauses.append(where_clause)
                
                elif filter_type == 'limit':
                    # Handle LIMIT clause
                    limit_value = entities[filter_type]
                    sql_modifications.append(f"LIMIT {limit_value}")
                
                elif filter_type == 'threshold':
                    # Handle threshold in HAVING or WHERE clauses
                    threshold_value = entities[filter_type]
                    if 'payers' in intent:
                        where_clauses.append(f"WHERE unique_customers > {threshold_value}")
                    elif 'immunizations' in intent:
                        # This is handled in the base SQL template
                        base_sql = base_sql.replace('{threshold}', threshold_value)
                
                elif filter_type == 'year':
                    # Handle year filtering
                    year_value = entities[filter_type]
                    where_clause = filter_template.format(value=year_value)
                    where_clauses.append(where_clause)
                
                elif filter_template:
                    # Standard filter handling
                    where_clause = filter_template.format(value=entities[filter_type])
                    where_clauses.append(where_clause)
        
        # Combine base SQL with filters
        if where_clauses:
            if 'WHERE' in base_sql:
                sql = base_sql + ' AND ' + ' AND '.join(where_clauses)
            else:
                sql = base_sql + ' ' + ' AND '.join(where_clauses)
        else:
            sql = base_sql
        
        # Add SQL modifications (LIMIT, etc.)
        for modification in sql_modifications:
            sql += ' ' + modification
        
        # Add default LIMIT for list queries if not already specified
        if intent.startswith('list_') and 'LIMIT' not in sql:
            sql += ' LIMIT 100'
        
        # Add default LIMIT for top queries if not already specified
        if intent.startswith('top_') and 'LIMIT' not in sql:
            sql += ' LIMIT 5'  # Default top 5
        
        return sql
    
    def get_supported_intents(self) -> List[str]:
        """Get list of supported query intents."""
        return list(self.intent_patterns.keys())