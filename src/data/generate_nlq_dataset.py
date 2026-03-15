#!/usr/bin/env python3
"""
NL→SQL Dataset Generator for Clinical NLQ Project
Generates a fresh training/validation/test dataset by:
1. Connecting to the PostgreSQL clinical_data DB
2. Sampling real values (conditions, medications, providers, states)
3. Generating diverse NL→SQL pairs from those real values
4. Writing train/val/test JSON files (70/15/15 split)

Run from project root:
    python src/data/generate_nlq_dataset.py

Output: data/processed/final_merged_dataset/
"""

import os
import sys
import json
import random
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Any

import psycopg2
from urllib.parse import quote_plus

# ── Setup ──────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# Load .env
_env = Path(__file__).parent.parent.parent / ".env"
if _env.exists():
    for line in _env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

DB_CONFIG = {
    'host':     os.getenv('DB_HOST', 'localhost'),
    'port':     int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'medical'),
    'user':     os.getenv('DB_USERNAME', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'Pass@123'),
}

OUTPUT_DIR = Path(__file__).parent.parent.parent / "data/processed/final_merged_dataset"

SCHEMA_HEADER = (
    "Database Schema: clinical_data\n"
    "Tables: patients, organizations, providers, encounters, conditions, "
    "medications, procedures, observations, allergies, careplans, immunizations, claims, payers\n"
    "Key relationships: \n"
    "- patients.id -> encounters.patient_id\n"
    "- providers.id -> encounters.provider_id  \n"
    "- organizations.id -> providers.organization_id\n"
    "- encounters.id -> conditions.encounter_id\n"
    "- encounters.id -> medications.encounter_id\n"
    "- encounters.id -> procedures.encounter_id\n"
    "- encounters.id -> observations.encounter_id\n"
    "- payers.id -> claims.payer_id"
)


def make_input(nl: str) -> str:
    return f"translate to sql: {nl} {SCHEMA_HEADER}"


# ──────────────────────────────────────────────────────────────────────────────
class DatasetGenerator:

    def __init__(self):
        self.conn = None
        self.conditions: List[str] = []
        self.medications: List[str] = []
        self.provider_names: List[str] = []
        self.states: List[str] = []
        self.specialties: List[str] = []
        self.org_states: List[str] = []

    # ── DB helpers ─────────────────────────────────────────────────────────────

    def connect(self) -> bool:
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.conn.autocommit = True
            logger.info("✅ Connected to database")
            return True
        except Exception as e:
            logger.error(f"❌ DB connection failed: {e}")
            return False

    def _query(self, sql: str) -> List[Any]:
        cur = self.conn.cursor()
        cur.execute(sql)
        rows = [r[0] for r in cur.fetchall()]
        cur.close()
        return rows

    def sample_real_values(self):
        """Pull real values from the database for use in queries."""
        logger.info("📥 Sampling real values from DB...")

        try:
            self.conditions = self._query(
                "SELECT description FROM clinical_data.conditions "
                "WHERE description IS NOT NULL GROUP BY description ORDER BY RANDOM() LIMIT 80"
            )
            logger.info(f"  Conditions: {len(self.conditions)}")
        except Exception as e:
            logger.warning(f"  Conditions fallback: {e}")
            self.conditions = [
                "Diabetes", "Hypertension", "Asthma", "COPD", "Obesity",
                "Anxiety", "Depression", "Arthritis", "Stroke", "Migraine",
                "Type 2 Diabetes", "Breast Cancer", "Heart Disease",
                "Fibromyalgia", "Epilepsy", "Endometriosis", "Chronic Pain",
                "Irritable Bowel Syndrome", "Overweight", "Cataracts",
                "Tinnitus", "Thyroid Disease", "Influenza", "COVID-19",
            ]

        try:
            self.medications = self._query(
                "SELECT description FROM clinical_data.medications "
                "WHERE description IS NOT NULL GROUP BY description ORDER BY RANDOM() LIMIT 80"
            )
            logger.info(f"  Medications: {len(self.medications)}")
        except Exception as e:
            logger.warning(f"  Medications fallback: {e}")
            self.medications = [
                "Metformin", "Amlodipine", "Lisinopril", "Omeprazole",
                "Atorvastatin", "Losartan", "Warfarin", "Insulin",
                "Bupropion", "Hydrochlorothiazide", "Clindamycin",
                "Meloxicam", "Trimethoprim", "Verapamil", "Indapamide",
            ]

        try:
            self.provider_names = self._query(
                "SELECT SPLIT_PART(name, ' ', 2) as last "
                "FROM clinical_data.providers WHERE name IS NOT NULL "
                "AND SPLIT_PART(name, ' ', 2) != '' GROUP BY SPLIT_PART(name, ' ', 2) ORDER BY RANDOM() LIMIT 60"
            )
            logger.info(f"  Provider last names: {len(self.provider_names)}")
        except Exception as e:
            logger.warning(f"  Provider names fallback: {e}")
            self.provider_names = [
                "Smith", "Johnson", "Williams", "Brown", "Jones",
                "Miller", "Davis", "Wilson", "Anderson", "Taylor",
                "Thomas", "Harris", "Martin", "Thompson", "Garcia",
                "Martinez", "Robinson", "Clark", "Rodriguez", "Lewis",
                "Walker", "Hall", "Allen", "Young", "Hernandez",
                "King", "Wright", "Lopez", "Hill", "Scott",
                "Green", "Adams", "Baker", "Nelson", "Carter",
                "Mitchell", "Perez", "Roberts", "Turner", "Phillips",
                "Campbell", "Parker", "Evans", "Edwards", "Collins",
                "Stewart", "Sanchez", "Morris", "Rogers", "Reed",
                "Cook", "Morgan", "Bell", "Murphy", "Bailey",
                "Rivera", "Cooper", "Richardson", "Cox", "Howard",
                "Ward", "Torres", "Peterson", "Gray", "Ramirez",
                "James", "Watson", "Brooks", "Kelly", "Sanders",
                "Price", "Bennett", "Wood", "Barnes", "Ross",
                "Henderson", "Coleman", "Jenkins", "Perry", "Powell",
                "Long", "Patterson", "Hughes", "Flores", "Washington",
                "Butler", "Simmons", "Foster", "Gonzales", "Bryant",
                "Alexander", "Russell", "Griffin", "Diaz", "Hayes",
                "Myers", "Ford", "Hamilton", "Graham", "Sullivan",
                "Wallace", "Woods", "Cole", "West", "Jordan",
                "Owens", "Reynolds", "Fisher", "Ellis", "Harrison",
            ]

        # Always use full state list for diversity
        self.states = [
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
        ]
        logger.info(f"  States: {len(self.states)} (full US list)")

        try:
            self.specialties = self._query(
                "SELECT speciality FROM clinical_data.providers "
                "WHERE speciality IS NOT NULL AND speciality != '' GROUP BY speciality ORDER BY RANDOM() LIMIT 40"
            )
            logger.info(f"  Specialties: {len(self.specialties)}")
        except Exception:
            self.specialties = [
                "General Practice", "Cardiology", "Endocrinology",
                "Gastroenterology", "Neurology", "Oncology",
                "Orthopedics", "Pulmonology", "Obstetrics",
                "Pathology", "Pain Management", "Cardiac Surgery",
                "Vascular Surgery", "Thoracic Surgery", "Ophthalmology",
            ]
        if not self.specialties:
            self.specialties = [
                "General Practice", "Cardiology", "Endocrinology",
                "Gastroenterology", "Neurology", "Oncology",
                "Orthopedics", "Pulmonology", "Obstetrics",
                "Pathology", "Pain Management", "Cardiac Surgery",
                "Vascular Surgery", "Thoracic Surgery", "Ophthalmology",
            ]

        self.org_states = self.states[:30] if self.states else ["CA", "TX", "NY", "FL", "IL"]
        logger.info("✅ Real values sampled")

    # ── Template factories ─────────────────────────────────────────────────────

    def _patient_state_queries(self) -> List[Tuple[str, str]]:
        pairs = []
        templates = [
            ("Get patients in {s} state",
             "SELECT first_name, last_name, city, state FROM clinical_data.patients WHERE state = '{s}' ORDER BY city, last_name"),
            ("List patients located in {s}",
             "SELECT first_name, last_name, city, state FROM clinical_data.patients WHERE state = '{s}' ORDER BY city, last_name"),
            ("Show patients from {s}",
             "SELECT first_name, last_name, city, state FROM clinical_data.patients WHERE state = '{s}' ORDER BY city, last_name"),
            ("Find patients in {s}",
             "SELECT first_name, last_name, city, state FROM clinical_data.patients WHERE state = '{s}' ORDER BY city, last_name"),
            ("Get patients from {s}",
             "SELECT first_name, last_name, city FROM clinical_data.patients WHERE state = '{s}' ORDER BY last_name"),
        ]
        for s in random.sample(self.states, min(len(self.states), 30)):
            nl_tmpl, sql_tmpl = random.choice(templates)
            pairs.append((nl_tmpl.format(s=s), sql_tmpl.format(s=s)))
        return pairs

    def _provider_state_queries(self) -> List[Tuple[str, str]]:
        pairs = []
        templates = [
            ("Get providers in {s} state",
             "SELECT name, speciality, city FROM clinical_data.providers WHERE state = '{s}' ORDER BY name"),
            ("Find providers located in {s}",
             "SELECT name, speciality FROM clinical_data.providers WHERE state = '{s}' ORDER BY name"),
            ("Show providers in {s}",
             "SELECT name, speciality, city FROM clinical_data.providers WHERE state = '{s}' ORDER BY name"),
            ("List providers from {s}",
             "SELECT name, speciality, city FROM clinical_data.providers WHERE state = '{s}' ORDER BY name"),
            ("Find providers in {s}",
             "SELECT name, speciality FROM clinical_data.providers WHERE state = '{s}' ORDER BY name"),
        ]
        for s in random.sample(self.states, min(len(self.states), 30)):
            nl_tmpl, sql_tmpl = random.choice(templates)
            pairs.append((nl_tmpl.format(s=s), sql_tmpl.format(s=s)))
        return pairs

    def _org_state_queries(self) -> List[Tuple[str, str]]:
        pairs = []
        for s in random.sample(self.org_states, min(len(self.org_states), 20)):
            templates = [
                (f"Show organizations based in {s}",
                 f"SELECT name, city, state FROM clinical_data.organizations WHERE state = '{s}' ORDER BY name"),
                (f"List organizations in {s}",
                 f"SELECT name, city FROM clinical_data.organizations WHERE state = '{s}' ORDER BY name"),
                (f"Get organizations in {s} state",
                 f"SELECT name, city FROM clinical_data.organizations WHERE state = '{s}' ORDER BY name"),
                (f"List organizations located in {s}",
                 f"SELECT name, city FROM clinical_data.organizations WHERE state = '{s}' ORDER BY name"),
                (f"Show organizations from {s}",
                 f"SELECT name, city FROM clinical_data.organizations WHERE state = '{s}' ORDER BY name"),
            ]
            pairs.append(random.choice(templates))
        return pairs

    def _condition_queries(self) -> List[Tuple[str, str]]:
        pairs = []
        for cond in random.sample(self.conditions, min(len(self.conditions), 40)):
            c = cond.replace("'", "''")   # SQL-escape
            templates = [
                (f"Find patients with {cond}",
                 f"SELECT DISTINCT p.first_name, p.last_name, c.start_date FROM clinical_data.patients p "
                 f"JOIN clinical_data.encounters e ON p.id = e.patient_id "
                 f"JOIN clinical_data.conditions c ON e.id = c.encounter_id "
                 f"WHERE c.description ILIKE '%{c}%' ORDER BY p.last_name"),
                (f"Show patients diagnosed with {cond}",
                 f"SELECT DISTINCT p.first_name, p.last_name, c.start_date FROM clinical_data.patients p "
                 f"JOIN clinical_data.encounters e ON p.id = e.patient_id "
                 f"JOIN clinical_data.conditions c ON e.id = c.encounter_id "
                 f"WHERE c.description ILIKE '%{c}%' ORDER BY c.start_date DESC"),
                (f"List {cond} patients",
                 f"SELECT DISTINCT p.first_name, p.last_name FROM clinical_data.patients p "
                 f"JOIN clinical_data.encounters e ON p.id = e.patient_id "
                 f"JOIN clinical_data.conditions c ON e.id = c.encounter_id "
                 f"WHERE c.description ILIKE '%{c}%' ORDER BY p.last_name"),
                (f"Show {cond} diagnoses",
                 f"SELECT p.first_name, p.last_name, c.start_date, pr.name as provider "
                 f"FROM clinical_data.patients p "
                 f"JOIN clinical_data.encounters e ON p.id = e.patient_id "
                 f"JOIN clinical_data.conditions c ON e.id = c.encounter_id "
                 f"JOIN clinical_data.providers pr ON e.provider_id = pr.id "
                 f"WHERE c.description ILIKE '%{c}%' ORDER BY c.start_date DESC"),
                (f"Get providers treating {cond}",
                 f"SELECT DISTINCT pr.name, pr.speciality FROM clinical_data.providers pr "
                 f"JOIN clinical_data.encounters e ON pr.id = e.provider_id "
                 f"JOIN clinical_data.conditions c ON e.id = c.encounter_id "
                 f"WHERE c.description ILIKE '%{c}%' ORDER BY pr.name"),
            ]
            pairs.append(random.choice(templates))
        return pairs

    def _medication_queries(self) -> List[Tuple[str, str]]:
        pairs = []
        for med in random.sample(self.medications, min(len(self.medications), 40)):
            m = med.replace("'", "''")
            name_short = med.split()[0] if ' ' in med else med
            templates = [
                (f"Find patients taking {name_short}",
                 f"SELECT DISTINCT p.first_name, p.last_name FROM clinical_data.patients p "
                 f"JOIN clinical_data.encounters e ON p.id = e.patient_id "
                 f"JOIN clinical_data.medications m ON e.id = m.encounter_id "
                 f"WHERE m.description ILIKE '%{m}%' ORDER BY p.last_name"),
                (f"List patients on {name_short}",
                 f"SELECT DISTINCT p.first_name, p.last_name FROM clinical_data.patients p "
                 f"JOIN clinical_data.encounters e ON p.id = e.patient_id "
                 f"JOIN clinical_data.medications m ON e.id = m.encounter_id "
                 f"WHERE m.description ILIKE '%{m}%' ORDER BY p.last_name"),
                (f"Get {name_short} users",
                 f"SELECT DISTINCT p.first_name, p.last_name, m.start_date FROM clinical_data.patients p "
                 f"JOIN clinical_data.encounters e ON p.id = e.patient_id "
                 f"JOIN clinical_data.medications m ON e.id = m.encounter_id "
                 f"WHERE m.description ILIKE '%{m}%' ORDER BY m.start_date DESC"),
                (f"Show {name_short} prescriptions",
                 f"SELECT p.first_name, p.last_name, m.start_date, pr.name as prescriber "
                 f"FROM clinical_data.patients p "
                 f"JOIN clinical_data.encounters e ON p.id = e.patient_id "
                 f"JOIN clinical_data.medications m ON e.id = m.encounter_id "
                 f"JOIN clinical_data.providers pr ON e.provider_id = pr.id "
                 f"WHERE m.description ILIKE '%{m}%' ORDER BY m.start_date DESC"),
                (f"Show providers prescribing {name_short}",
                 f"SELECT DISTINCT pr.name, pr.speciality FROM clinical_data.providers pr "
                 f"JOIN clinical_data.encounters e ON pr.id = e.provider_id "
                 f"JOIN clinical_data.medications m ON e.id = m.encounter_id "
                 f"WHERE m.description ILIKE '%{m}%' ORDER BY pr.name"),
                (f"Show {name_short} prescription trends",
                 f"SELECT DATE_TRUNC('month', m.start_date) as month, COUNT(*) as prescription_count "
                 f"FROM clinical_data.medications m "
                 f"WHERE m.description ILIKE '%{m}%' "
                 f"GROUP BY DATE_TRUNC('month', m.start_date) ORDER BY month"),
            ]
            pairs.append(random.choice(templates))
        return pairs

    def _provider_name_queries(self) -> List[Tuple[str, str]]:
        pairs = []
        for prov in random.sample(self.provider_names, min(len(self.provider_names), 50)):
            p = prov.replace("'", "''")
            templates = [
                (f"Show patients seen by Dr. {prov}",
                 f"SELECT DISTINCT p.first_name, p.last_name FROM clinical_data.patients p "
                 f"JOIN clinical_data.encounters e ON p.id = e.patient_id "
                 f"JOIN clinical_data.providers pr ON e.provider_id = pr.id "
                 f"WHERE pr.name ILIKE '%{p}%' ORDER BY p.last_name"),
                (f"Find patients treated by {prov}",
                 f"SELECT DISTINCT p.first_name, p.last_name, e.start_time as start_date "
                 f"FROM clinical_data.patients p "
                 f"JOIN clinical_data.encounters e ON p.id = e.patient_id "
                 f"JOIN clinical_data.providers pr ON e.provider_id = pr.id "
                 f"WHERE pr.name ILIKE '%{p}%' ORDER BY e.start_time DESC"),
                (f"Get patients of Dr. {prov}",
                 f"SELECT DISTINCT p.first_name, p.last_name FROM clinical_data.patients p "
                 f"JOIN clinical_data.encounters e ON p.id = e.patient_id "
                 f"JOIN clinical_data.providers pr ON e.provider_id = pr.id "
                 f"WHERE pr.name ILIKE '%{p}%' ORDER BY p.last_name"),
                (f"Show visits to provider {prov}",
                 f"SELECT p.first_name, p.last_name, e.start_time as start_date, e.encounter_class "
                 f"FROM clinical_data.patients p "
                 f"JOIN clinical_data.encounters e ON p.id = e.patient_id "
                 f"JOIN clinical_data.providers pr ON e.provider_id = pr.id "
                 f"WHERE pr.name ILIKE '%{p}%' ORDER BY e.start_time DESC"),
                (f"Find encounters with provider {prov}",
                 f"SELECT e.start_time as start_date, e.encounter_class, p.first_name, p.last_name "
                 f"FROM clinical_data.encounters e "
                 f"JOIN clinical_data.patients p ON e.patient_id = p.id "
                 f"JOIN clinical_data.providers pr ON e.provider_id = pr.id "
                 f"WHERE pr.name ILIKE '%{p}%' ORDER BY e.start_time DESC"),
                (f"List encounters with provider {prov}",
                 f"SELECT e.start_time as start_date, e.encounter_class, p.first_name, p.last_name "
                 f"FROM clinical_data.encounters e "
                 f"JOIN clinical_data.patients p ON e.patient_id = p.id "
                 f"JOIN clinical_data.providers pr ON e.provider_id = pr.id "
                 f"WHERE pr.name ILIKE '%{p}%' ORDER BY e.start_time DESC"),
                (f"List all visits to Dr. {prov}",
                 f"SELECT p.first_name, p.last_name, e.start_time as start_date, e.encounter_class "
                 f"FROM clinical_data.patients p "
                 f"JOIN clinical_data.encounters e ON p.id = e.patient_id "
                 f"JOIN clinical_data.providers pr ON e.provider_id = pr.id "
                 f"WHERE pr.name ILIKE '%{p}%' ORDER BY e.start_time DESC"),
            ]
            pairs.append(random.choice(templates))
        return pairs

    def _specialty_queries(self) -> List[Tuple[str, str]]:
        pairs = []
        for spec in random.sample(self.specialties, min(len(self.specialties), 20)):
            s = spec.replace("'", "''")
            short = spec.split()[0] if ' ' in spec else spec
            templates = [
                (f"Find {spec} providers",
                 f"SELECT name, speciality FROM clinical_data.providers WHERE speciality ILIKE '%{s}%' ORDER BY name"),
                (f"Get {short} physicians",
                 f"SELECT name, speciality, state FROM clinical_data.providers WHERE speciality ILIKE '%{s}%' ORDER BY name"),
                (f"Show {spec} specialists",
                 f"SELECT name, speciality, city FROM clinical_data.providers WHERE speciality ILIKE '%{s}%' ORDER BY name"),
                (f"List {short} doctors",
                 f"SELECT name, speciality FROM clinical_data.providers WHERE speciality ILIKE '%{s}%' ORDER BY name"),
                (f"Find all {spec} practitioners",
                 f"SELECT name, speciality, city, state FROM clinical_data.providers WHERE speciality ILIKE '%{s}%' ORDER BY name"),
            ]
            pairs.append(random.choice(templates))
        return pairs

    def _age_queries(self) -> List[Tuple[str, str]]:
        ages = [18, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 90, 100]
        pairs = []
        templates = [
            ("Find patients older than {a}",
             "SELECT first_name, last_name, birth_date FROM clinical_data.patients WHERE EXTRACT(YEAR FROM AGE(birth_date)) > {a} ORDER BY birth_date"),
            ("Show patients under {a} years old",
             "SELECT first_name, last_name, birth_date FROM clinical_data.patients WHERE EXTRACT(YEAR FROM AGE(birth_date)) < {a} ORDER BY birth_date DESC"),
            ("List patients exactly {a} years old",
             "SELECT first_name, last_name, birth_date FROM clinical_data.patients WHERE EXTRACT(YEAR FROM AGE(birth_date)) = {a} ORDER BY last_name"),
            ("Find patients {a} or younger",
             "SELECT first_name, last_name, birth_date FROM clinical_data.patients WHERE EXTRACT(YEAR FROM AGE(birth_date)) <= {a} ORDER BY birth_date DESC"),
            ("Get patients between {a} and {b} years old",
             "SELECT first_name, last_name, birth_date FROM clinical_data.patients WHERE EXTRACT(YEAR FROM AGE(birth_date)) BETWEEN {a} AND {b} ORDER BY birth_date"),
        ]
        for a in random.sample(ages, min(len(ages), 12)):
            tmpl_nl, tmpl_sql = random.choice(templates)
            b = a + 10
            pairs.append((tmpl_nl.format(a=a, b=b), tmpl_sql.format(a=a, b=b)))
        return pairs

    def _time_queries(self) -> List[Tuple[str, str]]:
        return [
            ("Display recent encounters",
             "SELECT patient_id, provider_id, start_time, encounter_class FROM clinical_data.encounters ORDER BY start_time DESC LIMIT 100"),
            ("Show encounters from the last 30 days",
             "SELECT start_time, encounter_class, patient_id FROM clinical_data.encounters WHERE start_time >= CURRENT_DATE - INTERVAL '30 days' ORDER BY start_time DESC"),
            ("Show encounters from the last 6 months",
             "SELECT start_time, encounter_class, patient_id FROM clinical_data.encounters WHERE start_time >= CURRENT_DATE - INTERVAL '6 months' ORDER BY start_time DESC"),
            ("Show encounters from the last 18 months",
             "SELECT start_time, encounter_class, patient_id FROM clinical_data.encounters WHERE start_time >= CURRENT_DATE - INTERVAL '18 months' ORDER BY start_time DESC"),
            ("List medications prescribed in the last 1 week",
             "SELECT description, start_date FROM clinical_data.medications WHERE start_date >= CURRENT_DATE - INTERVAL '1 week' ORDER BY start_date DESC"),
            ("List medications prescribed in the last 5 months",
             "SELECT description, start_date FROM clinical_data.medications WHERE start_date >= CURRENT_DATE - INTERVAL '5 months' ORDER BY start_date DESC"),
            ("List medications prescribed in the last 2 years",
             "SELECT description, start_date FROM clinical_data.medications WHERE start_date >= CURRENT_DATE - INTERVAL '2 years' ORDER BY start_date DESC"),
            ("Find medications in the past 6 months",
             "SELECT description, start_date FROM clinical_data.medications WHERE start_date >= CURRENT_DATE - INTERVAL '6 months' ORDER BY start_date DESC"),
            ("List recent procedures (3 months)",
             "SELECT description, date FROM clinical_data.procedures WHERE date >= CURRENT_DATE - INTERVAL '3 months' ORDER BY date DESC"),
            ("Show procedures from the last 1 day",
             "SELECT description, date FROM clinical_data.procedures WHERE date >= CURRENT_DATE - INTERVAL '1 day' ORDER BY date DESC"),
            ("Find patients born in the 2010s",
             "SELECT first_name, last_name, birth_date FROM clinical_data.patients WHERE EXTRACT(YEAR FROM birth_date) BETWEEN 2010 AND 2019 ORDER BY birth_date"),
            ("Find patients born in the 1990s",
             "SELECT first_name, last_name, birth_date FROM clinical_data.patients WHERE EXTRACT(YEAR FROM birth_date) BETWEEN 1990 AND 1999 ORDER BY birth_date"),
            ("Find patients born in the 1980s",
             "SELECT first_name, last_name, birth_date FROM clinical_data.patients WHERE EXTRACT(YEAR FROM birth_date) BETWEEN 1980 AND 1989 ORDER BY birth_date"),
        ]

    def _cost_queries(self) -> List[Tuple[str, str]]:
        costs = [5000, 10000, 15000, 20000, 30000, 50000, 100000]
        pairs = [
            ("Show patients spending more than $20000",
             "SELECT first_name, last_name, healthcare_expenses FROM clinical_data.patients WHERE healthcare_expenses > 20000 ORDER BY healthcare_expenses DESC"),
            ("Find patients with costs over $15000",
             "SELECT first_name, last_name, healthcare_expenses FROM clinical_data.patients WHERE healthcare_expenses > 15000 ORDER BY healthcare_expenses DESC"),
            ("Show patients with coverage gaps over $100,000",
             "SELECT first_name, last_name, healthcare_expenses, healthcare_coverage, "
             "(healthcare_expenses - healthcare_coverage) as gap FROM clinical_data.patients "
             "WHERE (healthcare_expenses - healthcare_coverage) > 100000 ORDER BY gap DESC"),
        ]
        for c in random.sample(costs, 4):
            pairs.append((
                f"Find patients with healthcare costs over ${c:,}",
                f"SELECT first_name, last_name, healthcare_expenses FROM clinical_data.patients "
                f"WHERE healthcare_expenses > {c} ORDER BY healthcare_expenses DESC"
            ))
        return pairs

    def _aggregate_queries(self) -> List[Tuple[str, str]]:
        return [
            ("How many patients do we have?",
             "SELECT COUNT(*) FROM clinical_data.patients"),
            ("How many providers are in the system?",
             "SELECT COUNT(*) FROM clinical_data.providers"),
            ("How many organizations are registered?",
             "SELECT COUNT(*) FROM clinical_data.organizations"),
            ("How many encounters have been recorded?",
             "SELECT COUNT(*) FROM clinical_data.encounters"),
            ("How many different medications are prescribed?",
             "SELECT COUNT(DISTINCT description) FROM clinical_data.medications"),
            ("What are the most common medical conditions?",
             "SELECT description, COUNT(*) as count FROM clinical_data.conditions "
             "GROUP BY description ORDER BY count DESC LIMIT 10"),
            ("Show the top 10 most common diagnoses",
             "SELECT description, COUNT(*) as patient_count FROM clinical_data.conditions "
             "GROUP BY description ORDER BY patient_count DESC LIMIT 10"),
            ("What are the most frequently prescribed medications?",
             "SELECT description, COUNT(*) as prescription_count FROM clinical_data.medications "
             "GROUP BY description ORDER BY prescription_count DESC LIMIT 10"),
            ("Show medication prescription counts",
             "SELECT description, COUNT(*) as prescription_count FROM clinical_data.medications "
             "GROUP BY description ORDER BY prescription_count DESC"),
            ("Find medications prescribed to more than 50 patients",
             "SELECT description, COUNT(DISTINCT encounter_id) as patient_count "
             "FROM clinical_data.medications GROUP BY description "
             "HAVING COUNT(DISTINCT encounter_id) > 50 ORDER BY patient_count DESC"),
            ("Find medications prescribed to more than 13 patients",
             "SELECT description, COUNT(DISTINCT encounter_id) as patient_count "
             "FROM clinical_data.medications GROUP BY description "
             "HAVING COUNT(DISTINCT encounter_id) > 13 ORDER BY patient_count DESC"),
            ("Find providers with more than 12 patients",
             "SELECT pr.name, COUNT(DISTINCT e.patient_id) as patient_count "
             "FROM clinical_data.providers pr "
             "JOIN clinical_data.encounters e ON pr.id = e.provider_id "
             "GROUP BY pr.id, pr.name HAVING COUNT(DISTINCT e.patient_id) > 12 ORDER BY patient_count DESC"),
            ("Find providers with more than 2 patients",
             "SELECT pr.name, COUNT(DISTINCT e.patient_id) as patient_count "
             "FROM clinical_data.providers pr "
             "JOIN clinical_data.encounters e ON pr.id = e.provider_id "
             "GROUP BY pr.id, pr.name HAVING COUNT(DISTINCT e.patient_id) > 2 ORDER BY patient_count DESC"),
            ("List providers having 9 or more patients",
             "SELECT pr.name, pr.speciality, COUNT(DISTINCT e.patient_id) as patients_count "
             "FROM clinical_data.providers pr "
             "JOIN clinical_data.encounters e ON pr.id = e.provider_id "
             "GROUP BY pr.id, pr.name, pr.speciality "
             "HAVING COUNT(DISTINCT e.patient_id) >= 9 ORDER BY patients_count DESC"),
            ("Retrieve patients information",
             "SELECT first_name, last_name, birth_date, gender FROM clinical_data.patients ORDER BY last_name, first_name"),
            ("List all specialties",
             "SELECT DISTINCT speciality FROM clinical_data.providers WHERE speciality IS NOT NULL ORDER BY speciality"),
            ("Find patients on 4 or more medications",
             "SELECT p.first_name, p.last_name, COUNT(DISTINCT m.description) as medication_count "
             "FROM clinical_data.patients p "
             "JOIN clinical_data.encounters e ON p.id = e.patient_id "
             "JOIN clinical_data.medications m ON e.id = m.encounter_id "
             "WHERE m.stop_date IS NULL GROUP BY p.id, p.first_name, p.last_name "
             "HAVING COUNT(DISTINCT m.description) >= 4 ORDER BY medication_count DESC"),
            ("Show complex medication interactions",
             "SELECT p.first_name, p.last_name, STRING_AGG(DISTINCT m.description, ', ') as medications "
             "FROM clinical_data.patients p "
             "JOIN clinical_data.encounters e ON p.id = e.patient_id "
             "JOIN clinical_data.medications m ON e.id = m.encounter_id "
             "WHERE m.stop_date IS NULL GROUP BY p.id, p.first_name, p.last_name "
             "HAVING COUNT(DISTINCT m.description) >= 4 ORDER BY p.last_name"),
            ("Find high-risk patients with multiple comorbidities",
             "SELECT p.first_name, p.last_name, COUNT(DISTINCT c.description) as comorbidity_count, "
             "STRING_AGG(DISTINCT c.description, ', ') as conditions "
             "FROM clinical_data.patients p "
             "JOIN clinical_data.encounters e ON p.id = e.patient_id "
             "JOIN clinical_data.conditions c ON e.id = c.encounter_id "
             "WHERE c.stop_date IS NULL GROUP BY p.id, p.first_name, p.last_name "
             "HAVING COUNT(DISTINCT c.description) >= 4 ORDER BY comorbidity_count DESC"),
        ]

    def _comorbidity_queries(self) -> List[Tuple[str, str]]:
        """Patients with BOTH condition A and condition B."""
        pairs = []
        cond_list = random.sample(self.conditions, min(len(self.conditions), 60))
        for i in range(0, len(cond_list) - 1, 2):
            c1 = cond_list[i]
            c2 = cond_list[i + 1]
            c1e = c1.replace("'", "''")
            c2e = c2.replace("'", "''")
            nl_tmpl = random.choice([
                f"Find patients with both {c1} and {c2}",
                f"Show patients having {c1} and {c2}",
                f"List patients diagnosed with both {c1} and {c2}",
            ])
            sql = (
                f"SELECT DISTINCT p.first_name, p.last_name FROM clinical_data.patients p "
                f"JOIN clinical_data.encounters e1 ON p.id = e1.patient_id "
                f"JOIN clinical_data.conditions c1 ON e1.id = c1.encounter_id "
                f"JOIN clinical_data.encounters e2 ON p.id = e2.patient_id "
                f"JOIN clinical_data.conditions c2 ON e2.id = c2.encounter_id "
                f"WHERE c1.description ILIKE '%{c1e}%' AND c2.description ILIKE '%{c2e}%' ORDER BY p.last_name"
            )
            pairs.append((nl_tmpl, sql))
        return pairs

    def _gender_queries(self) -> List[Tuple[str, str]]:
        return [
            ("Show all male patients",
             "SELECT first_name, last_name, birth_date FROM clinical_data.patients WHERE gender = 'M' ORDER BY last_name"),
            ("List female patients",
             "SELECT first_name, last_name, birth_date FROM clinical_data.patients WHERE gender = 'F' ORDER BY last_name"),
            ("Find all male patients",
             "SELECT first_name, last_name, birth_date, city FROM clinical_data.patients WHERE gender = 'M' ORDER BY last_name"),
            ("How many female patients are there?",
             "SELECT COUNT(*) FROM clinical_data.patients WHERE gender = 'F'"),
            ("What is the gender distribution of our patients?",
             "SELECT gender, COUNT(*) as count FROM clinical_data.patients GROUP BY gender ORDER BY count DESC"),
        ]

    # ── Main generation ────────────────────────────────────────────────────────
    def generate_all_pairs(self) -> List[Dict[str, str]]:
        all_pairs: List[Tuple[str, str]] = []

        all_pairs.extend(self._patient_state_queries())
        all_pairs.extend(self._provider_state_queries())
        all_pairs.extend(self._org_state_queries())
        all_pairs.extend(self._condition_queries())
        all_pairs.extend(self._medication_queries())
        all_pairs.extend(self._provider_name_queries())
        all_pairs.extend(self._specialty_queries())
        all_pairs.extend(self._age_queries())
        all_pairs.extend(self._time_queries())
        all_pairs.extend(self._cost_queries())
        all_pairs.extend(self._aggregate_queries())
        all_pairs.extend(self._comorbidity_queries())
        all_pairs.extend(self._gender_queries())

        # De-duplicate by NL question
        seen = set()
        unique = []
        for nl, sql in all_pairs:
            if nl not in seen:
                seen.add(nl)
                unique.append({'input_text': make_input(nl), 'target_text': sql})

        random.shuffle(unique)
        logger.info(f"✅ Generated {len(unique)} unique NL→SQL pairs")
        return unique

    # ── Output ────────────────────────────────────────────────────────────────
    def save_splits(self, pairs: List[Dict[str, str]]):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        n = len(pairs)
        train_end = int(n * 0.70)
        val_end   = int(n * 0.85)

        splits = {
            'train_data.json': pairs[:train_end],
            'val_data.json':   pairs[train_end:val_end],
            'test_data.json':  pairs[val_end:],
        }

        for fname, data in splits.items():
            path = OUTPUT_DIR / fname
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"  ✅ {fname}: {len(data)} examples → {path}")

        # Metadata
        meta = {
            'total': n,
            'train': len(splits['train_data.json']),
            'val':   len(splits['val_data.json']),
            'test':  len(splits['test_data.json']),
            'split': '70/15/15',
            'schema': 'clinical_data',
            'tables': 13,
            'generator': 'generate_nlq_dataset.py',
        }
        with open(OUTPUT_DIR / 'metadata.json', 'w') as f:
            json.dump(meta, f, indent=2)
        logger.info("  ✅ metadata.json written")

    def run(self):
        if not self.connect():
            logger.warning("⚠️  DB connection failed — using built-in fallback values")
            # Still works with built-in condition/medication lists
            self.conditions = [
                "Diabetes", "Hypertension", "Asthma", "COPD", "Obesity",
                "Anxiety", "Depression", "Arthritis", "Stroke", "Migraine",
                "Type 2 Diabetes", "Type 1 Diabetes", "Breast Cancer",
                "Heart Disease", "Fibromyalgia", "Epilepsy", "Endometriosis",
                "Chronic Pain", "Irritable Bowel Syndrome", "Overweight",
                "Cataracts", "Tinnitus", "Thyroid Disease", "Influenza",
                "COVID-19", "COPD", "Chronic Fatigue Syndrome", "PCOS",
                "Liver Disease", "Celiac Disease", "Coronary Heart Disease",
                "High Blood Pressure", "Osteoarthritis",
            ]
            self.medications = [
                "Metformin", "Amlodipine", "Lisinopril", "Omeprazole",
                "Atorvastatin", "Losartan", "Warfarin", "Insulin",
                "Bupropion", "Hydrochlorothiazide", "Clindamycin",
                "Meloxicam", "Trimethoprim", "Verapamil", "Indapamide",
                "Amoxicillin", "Metoprolol", "Gabapentin", "Sertraline",
                "Levothyroxine",
            ]
            self.states = [
                "AL", "AK", "AR", "CA", "CO", "CT", "FL", "GA",
                "IA", "ID", "IL", "KS", "MA", "MD", "MI", "MN",
                "MO", "MT", "NC", "NE", "NH", "NJ", "NM", "NY",
                "OH", "OK", "OR", "PA", "SC", "SD", "TN", "TX",
                "UT", "VT", "VA", "WA", "WI", "WV", "WY",
            ]
            self.provider_names = [
                "Smith", "Johnson", "Williams", "Brown", "Jones",
                "Miller", "Davis", "Wilson", "Anderson", "Taylor",
                "Thomas", "Harris", "Martin", "Thompson", "Garcia",
                "Martinez", "Robinson", "Clark", "Rodriguez", "Lewis",
                "Walker", "Hall", "Allen", "Young", "Hernandez",
                "King", "Wright", "Lopez", "Hill", "Scott",
                "Green", "Adams", "Baker", "Nelson", "Carter",
                "Mitchell", "Perez", "Roberts", "Turner", "Phillips",
                "Campbell", "Parker", "Evans", "Edwards", "Collins",
                "Stewart", "Sanchez", "Morris", "Rogers", "Reed",
            ]
            self.specialties = [
                "General Practice", "Cardiology", "Endocrinology",
                "Gastroenterology", "Neurology", "Oncology",
                "Orthopedics", "Pulmonology", "Obstetrics",
                "Pathology", "Pain Management", "Cardiac Surgery",
                "Vascular Surgery", "Thoracic Surgery", "Ophthalmology",
            ]
            self.org_states = self.states[:30]
        else:
            self.sample_real_values()

        pairs = self.generate_all_pairs()
        self.save_splits(pairs)
        logger.info(f"\n🎉 Dataset regenerated: {len(pairs)} total examples in {OUTPUT_DIR}")


# ──────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    random.seed(42)
    gen = DatasetGenerator()
    gen.run()
