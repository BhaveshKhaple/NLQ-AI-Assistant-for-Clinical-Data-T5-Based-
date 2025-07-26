#!/usr/bin/env python3
"""
Clinical NLQ Training Data Generator
Generates 1000 diverse Natural Language Question (NLQ) to SQL query pairs
for training the T5 model on clinical database queries.

Based on the Synthea clinical database schema with the following tables:
- patients, organizations, providers, payers, encounters, conditions, 
- medications, procedures, observations, immunizations, allergies, care_plans
"""

import json
import random
from typing import List, Dict, Tuple
from datetime import datetime, timedelta

class ClinicalNLQDataGenerator:
    def __init__(self):
        # Medical conditions from Synthea data
        self.conditions = [
            "Diabetes mellitus", "Hypertension", "Chronic pain", "Stress", 
            "Medication review due", "Full-time employment", "Higher education",
            "Chronic kidney disease", "Coronary heart disease", "Depression",
            "Anxiety disorder", "Asthma", "COPD", "Pneumonia", "Influenza",
            "Migraine", "Arthritis", "Osteoporosis", "Cancer", "Stroke",
            "Heart failure", "Atrial fibrillation", "Hyperlipidemia",
            "Obesity", "Sleep apnea", "Chronic fatigue syndrome"
        ]
        
        # Common medications from Synthea data
        self.medications = [
            "Acetaminophen", "Hydrocodone", "Oxycodone", "Fentanyl", 
            "Percocet", "Norinyl", "Medroxyprogesterone", "Insulin",
            "Metformin", "Lisinopril", "Atorvastatin", "Amlodipine",
            "Omeprazole", "Levothyroxine", "Albuterol", "Prednisone",
            "Warfarin", "Aspirin", "Ibuprofen", "Gabapentin"
        ]
        
        # Medical procedures
        self.procedures = [
            "Blood pressure measurement", "Blood glucose test", "Cholesterol screening",
            "Mammography", "Colonoscopy", "EKG", "Chest X-ray", "MRI scan",
            "CT scan", "Ultrasound", "Biopsy", "Surgery", "Physical therapy",
            "Vaccination", "Immunization", "Laboratory test", "Urinalysis"
        ]
        
        # Encounter types
        self.encounter_types = [
            "outpatient", "inpatient", "emergency", "urgent care", "wellness",
            "ambulatory", "home health", "telehealth", "observation"
        ]
        
        # Demographics
        self.genders = ["M", "F"]
        self.races = ["white", "black", "asian", "hispanic", "other"]
        self.states = ["Massachusetts", "California", "Texas", "Florida", "New York"]
        
        # Age ranges
        self.age_ranges = [
            ("pediatric", "< 18"),
            ("young adult", "18-30"), 
            ("adult", "31-50"),
            ("middle age", "51-65"),
            ("elderly", "> 65")
        ]

    def generate_basic_queries(self, count: int = 200) -> List[Dict]:
        """Generate basic count and filter queries (20%)"""
        queries = []
        
        basic_templates = [
            # Basic counts
            {
                "nlq_templates": [
                    "How many patients do we have in the database?",
                    "What is the total number of patients?",
                    "Count all patients in our system",
                    "How many patient records are there?"
                ],
                "sql": "SELECT COUNT(*) as patient_count FROM clinical_data.patients",
                "category": "basic_count"
            },
            {
                "nlq_templates": [
                    "How many {gender} patients do we have?",
                    "Count all {gender} patients",
                    "What is the number of {gender} patients?"
                ],
                "sql": "SELECT COUNT(*) as count FROM clinical_data.patients WHERE gender = '{gender_code}'",
                "category": "basic_filter",
                "variables": {"gender": ["male", "female"], "gender_code": ["M", "F"]}
            },
            {
                "nlq_templates": [
                    "How many encounters occurred this year?",
                    "Count encounters from this year",
                    "What is the total number of encounters in {year}?"
                ],
                "sql": "SELECT COUNT(*) as encounter_count FROM clinical_data.encounters WHERE EXTRACT(YEAR FROM start_time) = {year}",
                "category": "basic_count",
                "variables": {"year": ["2023", "2024"]}
            },
            {
                "nlq_templates": [
                    "How many conditions have been diagnosed?",
                    "Count all medical conditions",
                    "What is the total number of diagnoses?"
                ],
                "sql": "SELECT COUNT(*) as condition_count FROM clinical_data.conditions",
                "category": "basic_count"
            },
            {
                "nlq_templates": [
                    "Show me all patients from {state}",
                    "List patients living in {state}",
                    "Find all {state} patients"
                ],
                "sql": "SELECT first_name, last_name, city FROM clinical_data.patients WHERE state = '{state}'",
                "category": "basic_filter",
                "variables": {"state": self.states}
            },
            {
                "nlq_templates": [
                    "List all healthcare organizations",
                    "Show me all hospitals and clinics",
                    "What organizations are in our database?"
                ],
                "sql": "SELECT name, city, state FROM clinical_data.organizations ORDER BY name",
                "category": "basic_list"
            },
            {
                "nlq_templates": [
                    "How many medications are currently prescribed?",
                    "Count active medications",
                    "What is the number of ongoing prescriptions?"
                ],
                "sql": "SELECT COUNT(*) as active_medications FROM clinical_data.medications WHERE stop_date IS NULL",
                "category": "basic_count"
            },
            {
                "nlq_templates": [
                    "Show me patients born after {year}",
                    "List patients younger than {age}",
                    "Find patients born in {year} or later"
                ],
                "sql": "SELECT first_name, last_name, birth_date FROM clinical_data.patients WHERE birth_date > '{year}-01-01'",
                "category": "basic_filter",
                "variables": {"year": ["1990", "1980", "2000"], "age": ["30", "40", "20"]}
            }
        ]
        
        for template in basic_templates:
            for _ in range(count // len(basic_templates)):
                if len(queries) >= count:
                    break
                    
                nlq_template = random.choice(template["nlq_templates"])
                sql_template = template["sql"]
                
                if "variables" in template:
                    # Replace variables in templates
                    variables = {}
                    for var_name, var_options in template["variables"].items():
                        if isinstance(var_options, list):
                            if var_name == "gender_code":
                                # Special handling for gender mapping
                                gender_idx = list(template["variables"]["gender"]).index(variables.get("gender", "male"))
                                variables[var_name] = var_options[gender_idx]
                            else:
                                variables[var_name] = random.choice(var_options)
                    
                    nlq = nlq_template.format(**variables)
                    sql = sql_template.format(**variables)
                else:
                    nlq = nlq_template
                    sql = sql_template
                
                queries.append({
                    "nlq": nlq,
                    "sql": sql,
                    "category": template["category"]
                })
        
        return queries[:count]

    def generate_intermediate_queries(self, count: int = 250) -> List[Dict]:
        """Generate intermediate queries with joins and basic aggregations (25%)"""
        queries = []
        
        intermediate_templates = [
            {
                "nlq_templates": [
                    "Find all patients diagnosed with {condition}",
                    "Show me patients who have {condition}",
                    "List patients with a diagnosis of {condition}"
                ],
                "sql": "SELECT DISTINCT p.first_name, p.last_name, p.birth_date FROM clinical_data.patients p JOIN clinical_data.conditions c ON p.id = c.patient_id WHERE c.description ILIKE '%{condition}%'",
                "category": "join_filter",
                "variables": {"condition": self.conditions}
            },
            {
                "nlq_templates": [
                    "What are the most common conditions diagnosed?",
                    "Show me the top 10 most frequent diagnoses",
                    "List the most common medical conditions"
                ],
                "sql": "SELECT description, COUNT(*) as frequency FROM clinical_data.conditions GROUP BY description ORDER BY frequency DESC LIMIT 10",
                "category": "aggregation"
            },
            {
                "nlq_templates": [
                    "Which patients are taking {medication}?",
                    "Find patients prescribed {medication}",
                    "Show me who is on {medication}"
                ],
                "sql": "SELECT DISTINCT p.first_name, p.last_name FROM clinical_data.patients p JOIN clinical_data.medications m ON p.id = m.patient_id WHERE m.description ILIKE '%{medication}%'",
                "category": "join_filter",
                "variables": {"medication": self.medications}
            },
            {
                "nlq_templates": [
                    "How many encounters does each provider have?",
                    "Count encounters per healthcare provider",
                    "Show provider workload by encounter count"
                ],
                "sql": "SELECT pr.name, COUNT(e.id) as encounter_count FROM clinical_data.providers pr LEFT JOIN clinical_data.encounters e ON pr.id = e.provider_id GROUP BY pr.id, pr.name ORDER BY encounter_count DESC",
                "category": "aggregation"
            },
            {
                "nlq_templates": [
                    "What is the average age of our patients?",
                    "Calculate the mean patient age",
                    "Show me the average age in our database"
                ],
                "sql": "SELECT AVG(EXTRACT(YEAR FROM AGE(CURRENT_DATE, birth_date))) as average_age FROM clinical_data.patients",
                "category": "aggregation"
            },
            {
                "nlq_templates": [
                    "Which organizations have the most patients?",
                    "Show me hospitals with highest patient volume",
                    "Rank organizations by patient count"
                ],
                "sql": "SELECT o.name, COUNT(DISTINCT e.patient_id) as patient_count FROM clinical_data.organizations o JOIN clinical_data.encounters e ON o.id = e.organization_id GROUP BY o.id, o.name ORDER BY patient_count DESC",
                "category": "aggregation"
            },
            {
                "nlq_templates": [
                    "Find patients with multiple conditions",
                    "Show me patients who have more than one diagnosis",
                    "List patients with multiple medical conditions"
                ],
                "sql": "SELECT p.first_name, p.last_name, COUNT(c.id) as condition_count FROM clinical_data.patients p JOIN clinical_data.conditions c ON p.id = c.patient_id GROUP BY p.id, p.first_name, p.last_name HAVING COUNT(c.id) > 1 ORDER BY condition_count DESC",
                "category": "aggregation"
            },
            {
                "nlq_templates": [
                    "What is the total healthcare cost per patient?",
                    "Calculate total medical expenses by patient",
                    "Show me patient healthcare spending"
                ],
                "sql": "SELECT p.first_name, p.last_name, SUM(e.total_claim_cost) as total_cost FROM clinical_data.patients p JOIN clinical_data.encounters e ON p.id = e.patient_id WHERE e.total_claim_cost IS NOT NULL GROUP BY p.id, p.first_name, p.last_name ORDER BY total_cost DESC",
                "category": "financial_analysis"
            },
            {
                "nlq_templates": [
                    "Which medications are prescribed most frequently?",
                    "Show me the top prescribed drugs",
                    "List most common medications"
                ],
                "sql": "SELECT description, COUNT(*) as prescription_count FROM clinical_data.medications GROUP BY description ORDER BY prescription_count DESC LIMIT 15",
                "category": "aggregation"
            },
            {
                "nlq_templates": [
                    "Find patients treated by Dr. {provider_name}",
                    "Show me patients seen by {provider_name}",
                    "List {provider_name}'s patients"
                ],
                "sql": "SELECT DISTINCT p.first_name, p.last_name FROM clinical_data.patients p JOIN clinical_data.encounters e ON p.id = e.patient_id JOIN clinical_data.providers pr ON e.provider_id = pr.id WHERE pr.name ILIKE '%{provider_name}%'",
                "category": "join_filter",
                "variables": {"provider_name": ["Smith", "Johnson", "Williams", "Brown", "Jones"]}
            }
        ]
        
        for template in intermediate_templates:
            for _ in range(count // len(intermediate_templates)):
                if len(queries) >= count:
                    break
                    
                nlq_template = random.choice(template["nlq_templates"])
                sql_template = template["sql"]
                
                if "variables" in template:
                    variables = {}
                    for var_name, var_options in template["variables"].items():
                        variables[var_name] = random.choice(var_options)
                    
                    nlq = nlq_template.format(**variables)
                    sql = sql_template.format(**variables)
                else:
                    nlq = nlq_template
                    sql = sql_template
                
                queries.append({
                    "nlq": nlq,
                    "sql": sql,
                    "category": template["category"]
                })
        
        return queries[:count]

    def generate_advanced_queries(self, count: int = 300) -> List[Dict]:
        """Generate advanced queries with multi-joins and complex filters (30%)"""
        queries = []
        
        advanced_templates = [
            {
                "nlq_templates": [
                    "Which patients have both {condition1} and {condition2}?",
                    "Find patients diagnosed with both {condition1} and {condition2}",
                    "Show me patients who have {condition1} and also {condition2}"
                ],
                "sql": "SELECT p.first_name, p.last_name FROM clinical_data.patients p WHERE p.id IN (SELECT patient_id FROM clinical_data.conditions WHERE description ILIKE '%{condition1}%') AND p.id IN (SELECT patient_id FROM clinical_data.conditions WHERE description ILIKE '%{condition2}%')",
                "category": "complex_clinical",
                "variables": {"condition1": self.conditions[:10], "condition2": self.conditions[10:20]}
            },
            {
                "nlq_templates": [
                    "Find elderly patients with {condition} who are taking {medication}",
                    "Show me patients over 65 with {condition} on {medication}",
                    "List senior patients diagnosed with {condition} and prescribed {medication}"
                ],
                "sql": "SELECT DISTINCT p.first_name, p.last_name, EXTRACT(YEAR FROM AGE(CURRENT_DATE, p.birth_date)) as age FROM clinical_data.patients p JOIN clinical_data.conditions c ON p.id = c.patient_id JOIN clinical_data.medications m ON p.id = m.patient_id WHERE EXTRACT(YEAR FROM AGE(CURRENT_DATE, p.birth_date)) > 65 AND c.description ILIKE '%{condition}%' AND m.description ILIKE '%{medication}%'",
                "category": "complex_clinical",
                "variables": {"condition": self.conditions, "medication": self.medications}
            },
            {
                "nlq_templates": [
                    "What is the average cost of {encounter_type} visits by organization?",
                    "Calculate mean {encounter_type} encounter costs per hospital",
                    "Show me average {encounter_type} visit expenses by facility"
                ],
                "sql": "SELECT o.name as organization, COUNT(e.id) as total_encounters, AVG(e.total_claim_cost) as avg_cost_per_encounter FROM clinical_data.organizations o JOIN clinical_data.encounters e ON o.id = e.organization_id WHERE e.encounter_class = '{encounter_type}' AND e.total_claim_cost IS NOT NULL GROUP BY o.id, o.name ORDER BY avg_cost_per_encounter DESC",
                "category": "financial_analysis",
                "variables": {"encounter_type": self.encounter_types}
            },
            {
                "nlq_templates": [
                    "Which providers specialize in {specialty} and have seen more than {min_patients} patients?",
                    "Find {specialty} specialists with high patient volume (>{min_patients} patients)",
                    "Show me busy {specialty} providers with over {min_patients} patients"
                ],
                "sql": "SELECT pr.name, pr.speciality, COUNT(DISTINCT e.patient_id) as patient_count FROM clinical_data.providers pr JOIN clinical_data.encounters e ON pr.id = e.provider_id WHERE pr.speciality ILIKE '%{specialty}%' GROUP BY pr.id, pr.name, pr.speciality HAVING COUNT(DISTINCT e.patient_id) > {min_patients} ORDER BY patient_count DESC",
                "category": "provider_analysis",
                "variables": {"specialty": ["cardiology", "internal medicine", "family medicine", "pediatrics", "surgery"], "min_patients": ["5", "10", "15", "20"]}
            },
            {
                "nlq_templates": [
                    "Find patients who had {procedure} and were later diagnosed with {condition}",
                    "Show me patients with {procedure} followed by {condition} diagnosis",
                    "List patients who got {condition} after having {procedure}"
                ],
                "sql": "SELECT DISTINCT p.first_name, p.last_name FROM clinical_data.patients p JOIN clinical_data.procedures pr ON p.id = pr.patient_id JOIN clinical_data.conditions c ON p.id = c.patient_id WHERE pr.description ILIKE '%{procedure}%' AND c.description ILIKE '%{condition}%' AND pr.date < c.start_date",
                "category": "temporal_analysis",
                "variables": {"procedure": self.procedures, "condition": self.conditions}
            },
            {
                "nlq_templates": [
                    "What is the readmission rate for patients with {condition}?",
                    "Calculate how often {condition} patients return within 30 days",
                    "Show me 30-day readmission rates for {condition}"
                ],
                "sql": "WITH condition_patients AS (SELECT DISTINCT patient_id FROM clinical_data.conditions WHERE description ILIKE '%{condition}%'), patient_encounters AS (SELECT e.patient_id, e.start_time, LAG(e.start_time) OVER (PARTITION BY e.patient_id ORDER BY e.start_time) as prev_encounter FROM clinical_data.encounters e WHERE e.patient_id IN (SELECT patient_id FROM condition_patients)) SELECT COUNT(CASE WHEN start_time - prev_encounter <= INTERVAL '30 days' THEN 1 END)::FLOAT / COUNT(*)::FLOAT * 100 as readmission_rate_percent FROM patient_encounters WHERE prev_encounter IS NOT NULL",
                "category": "complex_clinical",
                "variables": {"condition": self.conditions}
            },
            {
                "nlq_templates": [
                    "Which patients have the highest medication costs?",
                    "Show me patients with most expensive prescriptions",
                    "Find patients spending the most on medications"
                ],
                "sql": "SELECT p.first_name, p.last_name, SUM(m.total_cost) as total_medication_cost, COUNT(m.id) as medication_count FROM clinical_data.patients p JOIN clinical_data.medications m ON p.id = m.patient_id WHERE m.total_cost IS NOT NULL GROUP BY p.id, p.first_name, p.last_name ORDER BY total_medication_cost DESC LIMIT 20",
                "category": "financial_analysis"
            },
            {
                "nlq_templates": [
                    "Find patients with {condition} who haven't had an encounter in the last {months} months",
                    "Show me {condition} patients who haven't been seen recently (>{months} months)",
                    "List {condition} patients overdue for visits (last seen >{months} months ago)"
                ],
                "sql": "SELECT DISTINCT p.first_name, p.last_name, MAX(e.start_time) as last_encounter FROM clinical_data.patients p JOIN clinical_data.conditions c ON p.id = c.patient_id LEFT JOIN clinical_data.encounters e ON p.id = e.patient_id WHERE c.description ILIKE '%{condition}%' GROUP BY p.id, p.first_name, p.last_name HAVING MAX(e.start_time) < CURRENT_DATE - INTERVAL '{months} months' OR MAX(e.start_time) IS NULL ORDER BY last_encounter ASC NULLS FIRST",
                "category": "care_management",
                "variables": {"condition": self.conditions, "months": ["6", "12", "18", "24"]}
            }
        ]
        
        for template in advanced_templates:
            for _ in range(count // len(advanced_templates)):
                if len(queries) >= count:
                    break
                    
                nlq_template = random.choice(template["nlq_templates"])
                sql_template = template["sql"]
                
                if "variables" in template:
                    variables = {}
                    for var_name, var_options in template["variables"].items():
                        variables[var_name] = random.choice(var_options)
                    
                    nlq = nlq_template.format(**variables)
                    sql = sql_template.format(**variables)
                else:
                    nlq = nlq_template
                    sql = sql_template
                
                queries.append({
                    "nlq": nlq,
                    "sql": sql,
                    "category": template["category"]
                })
        
        return queries[:count]

    def generate_complex_analytical_queries(self, count: int = 150) -> List[Dict]:
        """Generate complex analytical queries with window functions (15%)"""
        queries = []
        
        complex_templates = [
            {
                "nlq_templates": [
                    "Show me the trend of {condition} diagnoses over the years",
                    "How has {condition} diagnosis frequency changed over time?",
                    "Display yearly trends for {condition} cases"
                ],
                "sql": "SELECT EXTRACT(YEAR FROM start_date) as year, COUNT(*) as case_count, LAG(COUNT(*)) OVER (ORDER BY EXTRACT(YEAR FROM start_date)) as prev_year_count FROM clinical_data.conditions WHERE description ILIKE '%{condition}%' GROUP BY EXTRACT(YEAR FROM start_date) ORDER BY year",
                "category": "trend_analysis",
                "variables": {"condition": self.conditions}
            },
            {
                "nlq_templates": [
                    "Rank providers by their patient satisfaction scores",
                    "Show me top-performing providers by patient outcomes",
                    "List providers ranked by performance metrics"
                ],
                "sql": "SELECT pr.name, pr.speciality, COUNT(DISTINCT e.patient_id) as patient_count, AVG(e.total_claim_cost) as avg_cost, RANK() OVER (ORDER BY COUNT(DISTINCT e.patient_id) DESC) as patient_volume_rank FROM clinical_data.providers pr JOIN clinical_data.encounters e ON pr.id = e.provider_id WHERE e.total_claim_cost IS NOT NULL GROUP BY pr.id, pr.name, pr.speciality ORDER BY patient_volume_rank",
                "category": "provider_ranking"
            },
            {
                "nlq_templates": [
                    "Calculate the running total of healthcare costs by month",
                    "Show me cumulative healthcare spending over time",
                    "Display monthly healthcare cost accumulation"
                ],
                "sql": "SELECT DATE_TRUNC('month', start_time) as month, SUM(total_claim_cost) as monthly_cost, SUM(SUM(total_claim_cost)) OVER (ORDER BY DATE_TRUNC('month', start_time)) as cumulative_cost FROM clinical_data.encounters WHERE total_claim_cost IS NOT NULL GROUP BY DATE_TRUNC('month', start_time) ORDER BY month",
                "category": "financial_trend"
            },
            {
                "nlq_templates": [
                    "Find patients with the longest medication treatment durations",
                    "Show me patients on long-term medication therapy",
                    "List patients with extended medication regimens"
                ],
                "sql": "SELECT p.first_name, p.last_name, m.description, m.start_date, COALESCE(m.stop_date, CURRENT_DATE) as end_date, EXTRACT(DAYS FROM (COALESCE(m.stop_date, CURRENT_DATE) - m.start_date)) as duration_days, RANK() OVER (ORDER BY EXTRACT(DAYS FROM (COALESCE(m.stop_date, CURRENT_DATE) - m.start_date)) DESC) as duration_rank FROM clinical_data.patients p JOIN clinical_data.medications m ON p.id = m.patient_id WHERE m.start_date IS NOT NULL ORDER BY duration_days DESC LIMIT 20",
                "category": "medication_analysis"
            },
            {
                "nlq_templates": [
                    "Calculate patient risk scores based on condition count and age",
                    "Show me high-risk patients using clinical indicators",
                    "Rank patients by clinical risk factors"
                ],
                "sql": "SELECT p.first_name, p.last_name, EXTRACT(YEAR FROM AGE(CURRENT_DATE, p.birth_date)) as age, COUNT(c.id) as condition_count, (EXTRACT(YEAR FROM AGE(CURRENT_DATE, p.birth_date)) * 0.1 + COUNT(c.id) * 2) as risk_score, NTILE(5) OVER (ORDER BY (EXTRACT(YEAR FROM AGE(CURRENT_DATE, p.birth_date)) * 0.1 + COUNT(c.id) * 2) DESC) as risk_quintile FROM clinical_data.patients p LEFT JOIN clinical_data.conditions c ON p.id = c.patient_id GROUP BY p.id, p.first_name, p.last_name, p.birth_date ORDER BY risk_score DESC",
                "category": "risk_analysis"
            },
            {
                "nlq_templates": [
                    "Show me the distribution of encounter costs by percentile",
                    "Calculate cost percentiles for medical encounters",
                    "Display encounter cost distribution analysis"
                ],
                "sql": "SELECT encounter_class, PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY total_claim_cost) as q1_cost, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_claim_cost) as median_cost, PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total_claim_cost) as q3_cost, PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY total_claim_cost) as p90_cost FROM clinical_data.encounters WHERE total_claim_cost IS NOT NULL GROUP BY encounter_class ORDER BY median_cost DESC",
                "category": "cost_distribution"
            },
            {
                "nlq_templates": [
                    "Find seasonal patterns in {condition} diagnoses",
                    "Show me monthly trends for {condition} cases",
                    "Analyze seasonal variation in {condition} occurrence"
                ],
                "sql": "SELECT EXTRACT(MONTH FROM start_date) as month, TO_CHAR(TO_DATE(EXTRACT(MONTH FROM start_date)::text, 'MM'), 'Month') as month_name, COUNT(*) as case_count, AVG(COUNT(*)) OVER () as avg_monthly_cases, (COUNT(*) - AVG(COUNT(*)) OVER ()) / STDDEV(COUNT(*)) OVER () as z_score FROM clinical_data.conditions WHERE description ILIKE '%{condition}%' GROUP BY EXTRACT(MONTH FROM start_date) ORDER BY month",
                "category": "seasonal_analysis",
                "variables": {"condition": self.conditions}
            }
        ]
        
        for template in complex_templates:
            for _ in range(count // len(complex_templates)):
                if len(queries) >= count:
                    break
                    
                nlq_template = random.choice(template["nlq_templates"])
                sql_template = template["sql"]
                
                if "variables" in template:
                    variables = {}
                    for var_name, var_options in template["variables"].items():
                        variables[var_name] = random.choice(var_options)
                    
                    nlq = nlq_template.format(**variables)
                    sql = sql_template.format(**variables)
                else:
                    nlq = nlq_template
                    sql = sql_template
                
                queries.append({
                    "nlq": nlq,
                    "sql": sql,
                    "category": template["category"]
                })
        
        return queries[:count]

    def generate_temporal_queries(self, count: int = 100) -> List[Dict]:
        """Generate temporal analysis queries (10%)"""
        queries = []
        
        temporal_templates = [
            {
                "nlq_templates": [
                    "How long do patients typically take {medication}?",
                    "What is the average duration for {medication} prescriptions?",
                    "Calculate mean treatment time for {medication}"
                ],
                "sql": "SELECT AVG(EXTRACT(DAYS FROM (stop_date - start_date))) as avg_duration_days, COUNT(*) as prescription_count FROM clinical_data.medications WHERE description ILIKE '%{medication}%' AND stop_date IS NOT NULL AND start_date IS NOT NULL",
                "category": "temporal_analysis",
                "variables": {"medication": self.medications}
            },
            {
                "nlq_templates": [
                    "Find patients diagnosed with {condition} in the last {months} months",
                    "Show me recent {condition} diagnoses (last {months} months)",
                    "List new {condition} cases from the past {months} months"
                ],
                "sql": "SELECT p.first_name, p.last_name, c.start_date, c.description FROM clinical_data.patients p JOIN clinical_data.conditions c ON p.id = c.patient_id WHERE c.description ILIKE '%{condition}%' AND c.start_date >= CURRENT_DATE - INTERVAL '{months} months' ORDER BY c.start_date DESC",
                "category": "temporal_filter",
                "variables": {"condition": self.conditions, "months": ["3", "6", "12", "18"]}
            },
            {
                "nlq_templates": [
                    "What is the time between diagnosis and treatment for {condition}?",
                    "Calculate diagnosis-to-treatment time for {condition} patients",
                    "Show me treatment delay for {condition} cases"
                ],
                "sql": "SELECT p.first_name, p.last_name, c.start_date as diagnosis_date, MIN(m.start_date) as first_treatment_date, MIN(m.start_date) - c.start_date as days_to_treatment FROM clinical_data.patients p JOIN clinical_data.conditions c ON p.id = c.patient_id JOIN clinical_data.medications m ON p.id = m.patient_id WHERE c.description ILIKE '%{condition}%' AND m.start_date >= c.start_date GROUP BY p.id, p.first_name, p.last_name, c.start_date ORDER BY days_to_treatment DESC",
                "category": "care_timeline",
                "variables": {"condition": self.conditions}
            },
            {
                "nlq_templates": [
                    "Show me encounter frequency by day of the week",
                    "Which days have the most medical visits?",
                    "Display weekly patterns in healthcare encounters"
                ],
                "sql": "SELECT TO_CHAR(start_time, 'Day') as day_of_week, EXTRACT(DOW FROM start_time) as day_number, COUNT(*) as encounter_count FROM clinical_data.encounters GROUP BY EXTRACT(DOW FROM start_time), TO_CHAR(start_time, 'Day') ORDER BY day_number",
                "category": "temporal_pattern"
            },
            {
                "nlq_templates": [
                    "Find patients with gaps in care longer than {months} months",
                    "Show me patients with care discontinuity (>{months} months)",
                    "List patients with extended gaps between visits (>{months} months)"
                ],
                "sql": "WITH encounter_gaps AS (SELECT patient_id, start_time, LAG(start_time) OVER (PARTITION BY patient_id ORDER BY start_time) as prev_encounter, start_time - LAG(start_time) OVER (PARTITION BY patient_id ORDER BY start_time) as gap_duration FROM clinical_data.encounters) SELECT DISTINCT p.first_name, p.last_name, eg.gap_duration FROM clinical_data.patients p JOIN encounter_gaps eg ON p.id = eg.patient_id WHERE eg.gap_duration > INTERVAL '{months} months' ORDER BY eg.gap_duration DESC",
                "category": "care_gaps",
                "variables": {"months": ["6", "12", "18", "24"]}
            },
            {
                "nlq_templates": [
                    "Calculate patient age at first diagnosis of {condition}",
                    "What age are patients typically diagnosed with {condition}?",
                    "Show me age distribution for {condition} onset"
                ],
                "sql": "SELECT p.first_name, p.last_name, MIN(c.start_date) as first_diagnosis, EXTRACT(YEAR FROM AGE(MIN(c.start_date), p.birth_date)) as age_at_diagnosis FROM clinical_data.patients p JOIN clinical_data.conditions c ON p.id = c.patient_id WHERE c.description ILIKE '%{condition}%' GROUP BY p.id, p.first_name, p.last_name, p.birth_date ORDER BY age_at_diagnosis",
                "category": "age_analysis",
                "variables": {"condition": self.conditions}
            },
            {
                "nlq_templates": [
                    "Show me medication adherence patterns over time",
                    "Calculate how often patients refill prescriptions on time",
                    "Display medication compliance trends"
                ],
                "sql": "SELECT m.description, COUNT(*) as total_prescriptions, COUNT(CASE WHEN m.stop_date IS NOT NULL THEN 1 END) as completed_prescriptions, (COUNT(CASE WHEN m.stop_date IS NOT NULL THEN 1 END)::FLOAT / COUNT(*)::FLOAT * 100) as completion_rate FROM clinical_data.medications m GROUP BY m.description HAVING COUNT(*) > 5 ORDER BY completion_rate DESC",
                "category": "adherence_analysis"
            }
        ]
        
        for template in temporal_templates:
            for _ in range(count // len(temporal_templates)):
                if len(queries) >= count:
                    break
                    
                nlq_template = random.choice(template["nlq_templates"])
                sql_template = template["sql"]
                
                if "variables" in template:
                    variables = {}
                    for var_name, var_options in template["variables"].items():
                        variables[var_name] = random.choice(var_options)
                    
                    nlq = nlq_template.format(**variables)
                    sql = sql_template.format(**variables)
                else:
                    nlq = nlq_template
                    sql = sql_template
                
                queries.append({
                    "nlq": nlq,
                    "sql": sql,
                    "category": template["category"]
                })
        
        return queries[:count]

    def generate_all_queries(self) -> List[Dict]:
        """Generate all 1000 queries with the specified distribution"""
        print("Generating clinical NLQ training data...")
        
        all_queries = []
        
        # Generate queries according to distribution
        print("Generating basic queries (20%)...")
        all_queries.extend(self.generate_basic_queries(200))
        
        print("Generating intermediate queries (25%)...")
        all_queries.extend(self.generate_intermediate_queries(250))
        
        print("Generating advanced queries (30%)...")
        all_queries.extend(self.generate_advanced_queries(300))
        
        print("Generating complex analytical queries (15%)...")
        all_queries.extend(self.generate_complex_analytical_queries(150))
        
        print("Generating temporal queries (10%)...")
        all_queries.extend(self.generate_temporal_queries(100))
        
        # Add more queries if we're short of 1000
        if len(all_queries) < 1000:
            # Add a few more basic queries to reach exactly 1000
            needed = 1000 - len(all_queries)
            additional = self.generate_basic_queries(needed)
            all_queries.extend(additional)
        
        # Shuffle to mix categories
        random.shuffle(all_queries)
        
        # Ensure exactly 1000 queries
        return all_queries[:1000]

    def save_training_data(self, queries: List[Dict], filename: str = "clinical_nlq_training_data.json"):
        """Save the generated queries to a JSON file with metadata"""
        output_path = f"d:/projects/healthca/data/processed/{filename}"
        
        # Create directory if it doesn't exist
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Generate summary statistics
        categories = {}
        for query in queries:
            category = query['category']
            categories[category] = categories.get(category, 0) + 1
        
        # Create final dataset with metadata
        dataset = {
            "metadata": {
                "name": "Clinical NLQ to SQL Training Dataset",
                "description": "1000 diverse natural language questions paired with SQL queries for clinical database",
                "version": "1.0",
                "created_date": datetime.now().isoformat(),
                "total_examples": len(queries),
                "database_schema": "clinical_data (PostgreSQL)",
                "categories": categories,
                "distribution": {
                    "basic_queries": "20%",
                    "intermediate_queries": "25%", 
                    "advanced_queries": "30%",
                    "complex_analytical": "15%",
                    "temporal_queries": "10%"
                }
            },
            "data": queries
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        print(f"Training data saved to: {output_path}")
        
        print(f"\nGenerated {len(queries)} NLQ-SQL pairs:")
        for category, count in sorted(categories.items()):
            percentage = (count / len(queries)) * 100
            print(f"  {category}: {count} queries ({percentage:.1f}%)")
        
        return output_path

def main():
    """Main function to generate and save training data"""
    generator = ClinicalNLQDataGenerator()
    
    # Generate all queries
    queries = generator.generate_all_queries()
    
    # Save to file
    output_path = generator.save_training_data(queries)
    
    print(f"\n✅ Successfully generated 1000 clinical NLQ-SQL training pairs!")
    print(f"📁 File saved at: {output_path}")
    print(f"🎯 Ready for T5 model training!")

if __name__ == "__main__":
    main()