#!/usr/bin/env python3
"""
Gemini NLQ Pipeline
Simple, clean pipeline: Natural Language → Gemini → SQL → Execute → Results

This is the core engine for the Clinical NLQ Master's Project demo.
Architecture: NL Query → Gemini LLM → SQL → PostgreSQL → Results
"""

import os
import re
import time
import logging
from typing import Dict, Any, Optional

import psycopg2
import pandas as pd
from urllib.parse import quote_plus

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Full schema context given to Gemini on every request
# ─────────────────────────────────────────────────────────────────────────────
SCHEMA_CONTEXT = """
You are an expert SQL generator for a PostgreSQL clinical healthcare database.

DATABASE: medical
SCHEMA: clinical_data

TABLES AND KEY COLUMNS:

patients (id UUID, birth_date DATE, death_date DATE, first_name, last_name,
          gender, race, ethnicity, city, state, zip, marital_status,
          healthcare_expenses DECIMAL, healthcare_coverage DECIMAL, income DECIMAL)

organizations (id UUID, name, city, state, zip, phone, revenue, utilization)

providers (id UUID, organization_id→organizations, name, gender, speciality,
           city, state, zip, utilization)

payers (id UUID, name, ownership, city, state, amount_covered, amount_uncovered,
        revenue, covered_encounters, covered_medications, unique_customers)

encounters (id UUID, start_time TIMESTAMP, stop_time TIMESTAMP,
            patient_id→patients, organization_id→organizations,
            provider_id→providers, payer_id→payers,
            encounter_class, description, base_encounter_cost,
            total_claim_cost, payer_coverage, reason_description)

conditions (id UUID, start_date DATE, stop_date DATE,
            patient_id→patients, encounter_id→encounters,
            code, description TEXT)

medications (id UUID, start_date DATE, stop_date DATE,
             patient_id→patients, encounter_id→encounters, payer_id→payers,
             code, description TEXT, base_cost, total_cost, reason_description)

procedures (id UUID, date DATE, patient_id→patients, encounter_id→encounters,
            code, description TEXT, base_cost, reason_description)

observations (id UUID, date DATE, patient_id→patients, encounter_id→encounters,
              category, code, description TEXT, value, units, type)

immunizations (id UUID, date DATE, patient_id→patients, encounter_id→encounters,
               code, description TEXT, base_cost)

allergies (id UUID, start_date DATE, stop_date DATE,
           patient_id→patients, encounter_id→encounters,
           code, category, description1 TEXT, severity1)

care_plans (id UUID, start_date DATE, stop_date DATE,
            patient_id→patients, encounter_id→encounters,
            code, description TEXT, reason_description)

claims (id UUID, patient_id→patients, provider_id→providers,
        service_date DATE, diagnosis1..8)

KEY RELATIONSHIPS:
- patients.id → encounters.patient_id
- providers.id → encounters.provider_id
- organizations.id → providers.organization_id
- encounters.id → conditions.encounter_id
- encounters.id → medications.encounter_id
- encounters.id → procedures.encounter_id
- encounters.id → observations.encounter_id
- payers.id → claims.payer_id

IMPORTANT RULES:
1. Always prefix tables with schema: clinical_data.patients, clinical_data.encounters, etc.
2. Use DATE column for encounters: encounters has start_time (TIMESTAMP) — use start_time for date filters
3. For patient age: EXTRACT(YEAR FROM AGE(birth_date))
4. Use ILIKE for text searches (case-insensitive): description ILIKE '%Diabetes%'
5. Use DISTINCT to avoid duplicates when joining
6. Patient name columns: first_name, last_name (NOT full_name)
7. Provider specialty column is: speciality (note the spelling)
8. Return ONLY the SQL query, no markdown, no explanation, no code blocks
"""

SYSTEM_PROMPT = SCHEMA_CONTEXT + """
INSTRUCTION: Convert the following natural language question into a valid PostgreSQL SELECT query.
Output ONLY the raw SQL. Do NOT include ```sql, ```, explanations, or any other text.
"""


class GeminiNLQPipeline:
    """
    Clean NLQ pipeline: Natural Language → Gemini → SQL → Results

    This class is the single entry point for the Clinical NLQ demo.
    """

    def __init__(self):
        """Initialize the pipeline with Gemini API and DB config."""
        self.gemini_model = None
        self.db_conn = None
        self.initialized = False

        # DB config from environment / defaults
        self.db_config = {
            'host':     os.getenv('DB_HOST', 'localhost'),
            'port':     int(os.getenv('DB_PORT', '5432')),
            'database': os.getenv('DB_NAME', 'medical'),
            'user':     os.getenv('DB_USERNAME', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'Pass@123'),
        }

        self.api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')

        # Stats
        self.stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'total_time': 0.0,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Initialization
    # ─────────────────────────────────────────────────────────────────────────

    def initialize(self) -> Dict[str, Any]:
        """Initialize Gemini API connection. DB connection is lazy (per-query)."""
        if not GEMINI_AVAILABLE:
            return {
                'success': False,
                'error': 'google-generativeai not installed. Run: pip install google-generativeai'
            }

        if not self.api_key:
            return {
                'success': False,
                'error': 'No GEMINI_API_KEY found. Set it in .env or environment.'
            }

        try:
            genai.configure(api_key=self.api_key)

            self.gemini_model = genai.GenerativeModel(
                model_name='gemini-2.5-flash',
                generation_config={
                    'temperature': 0.1,     # Low for consistent SQL output
                    'top_p': 0.9,
                    'max_output_tokens': 1024,
                }
            )

            # Quick connection test
            test = self.gemini_model.generate_content("Return only: OK")
            if not test or not test.text:
                return {'success': False, 'error': 'Gemini API test failed'}

            self.initialized = True
            logger.info("✅ Gemini NLQ Pipeline initialized")
            return {'success': True, 'model': 'gemini-2.5-flash'}

        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return {'success': False, 'error': str(e)}

    # ─────────────────────────────────────────────────────────────────────────
    # Core: NL → SQL via Gemini
    # ─────────────────────────────────────────────────────────────────────────

    def generate_sql(self, natural_query: str) -> Dict[str, Any]:
        """
        Convert natural language query to SQL using Gemini.

        Args:
            natural_query: Plain English question about the clinical data

        Returns:
            dict with 'sql', 'success', 'generation_time', 'error'
        """
        if not self.initialized:
            return {'success': False, 'sql': '', 'error': 'Pipeline not initialized'}

        start = time.time()
        self.stats['total_queries'] += 1

        try:
            prompt = f"{SYSTEM_PROMPT}\n\nQuestion: {natural_query}\n\nSQL:"
            response = self.gemini_model.generate_content(prompt)
            generation_time = time.time() - start

            if not response or not response.text:
                self.stats['failed_queries'] += 1
                return {
                    'success': False,
                    'sql': '',
                    'generation_time': generation_time,
                    'error': 'Empty response from Gemini'
                }

            sql = self._clean_sql(response.text)

            if not self._is_valid_sql(sql):
                self.stats['failed_queries'] += 1
                return {
                    'success': False,
                    'sql': sql,
                    'generation_time': generation_time,
                    'error': f'Generated text does not look like valid SQL: {sql[:200]}'
                }

            self.stats['successful_queries'] += 1
            self.stats['total_time'] += generation_time
            logger.info(f"✅ SQL generated in {generation_time:.2f}s: {sql[:80]}...")

            return {
                'success': True,
                'sql': sql,
                'generation_time': generation_time,
                'model': 'gemini-2.5-flash',
                'natural_query': natural_query,
            }

        except Exception as e:
            generation_time = time.time() - start
            self.stats['failed_queries'] += 1
            logger.error(f"❌ SQL generation error: {e}")
            return {
                'success': False,
                'sql': '',
                'generation_time': generation_time,
                'error': str(e)
            }

    # ─────────────────────────────────────────────────────────────────────────
    # Database execution
    # ─────────────────────────────────────────────────────────────────────────

    def execute_sql(self, sql: str, max_rows: int = 500) -> Dict[str, Any]:
        """
        Execute SQL against PostgreSQL and return results as a DataFrame.

        Args:
            sql: Valid PostgreSQL SELECT query
            max_rows: Maximum rows to return

        Returns:
            dict with 'data' (DataFrame), 'row_count', 'success', 'execution_time', 'error'
        """
        start = time.time()

        try:
            conn = self._get_connection()
            if not conn:
                return {
                    'success': False,
                    'data': None,
                    'error': 'Could not connect to database. Check PostgreSQL is running.'
                }

            # Add LIMIT if not already present
            sql_limited = self._add_limit(sql, max_rows)

            df = pd.read_sql_query(sql_limited, conn)
            execution_time = time.time() - start

            logger.info(f"✅ Query executed: {len(df)} rows in {execution_time:.3f}s")
            return {
                'success': True,
                'data': df,
                'row_count': len(df),
                'execution_time': execution_time,
                'sql_executed': sql_limited,
            }

        except Exception as e:
            execution_time = time.time() - start
            logger.error(f"❌ SQL execution error: {e}")
            # Try to close broken connection
            self._close_connection()
            return {
                'success': False,
                'data': None,
                'row_count': 0,
                'execution_time': execution_time,
                'error': str(e)
            }

    def run_query(self, natural_query: str, execute: bool = True) -> Dict[str, Any]:
        """
        Full pipeline: NL → SQL → (optional) Execute → Results

        Args:
            natural_query: Plain English question
            execute: Whether to execute the SQL (True = full pipeline)

        Returns:
            dict with all results
        """
        result = {
            'natural_query': natural_query,
            'success': False,
            'sql': '',
            'data': None,
            'generation_time': 0.0,
            'execution_time': 0.0,
            'total_time': 0.0,
            'row_count': 0,
            'error': None,
        }

        # Step 1: Generate SQL
        gen = self.generate_sql(natural_query)
        result['sql'] = gen.get('sql', '')
        result['generation_time'] = gen.get('generation_time', 0.0)

        if not gen['success']:
            result['error'] = gen.get('error', 'SQL generation failed')
            return result

        # Step 2: Execute SQL
        if execute:
            exec_result = self.execute_sql(gen['sql'])
            result['data'] = exec_result.get('data')
            result['execution_time'] = exec_result.get('execution_time', 0.0)
            result['row_count'] = exec_result.get('row_count', 0)

            if not exec_result['success']:
                result['error'] = exec_result.get('error', 'SQL execution failed')
                result['total_time'] = result['generation_time'] + result['execution_time']
                return result

            result['success'] = True
        else:
            result['success'] = True

        result['total_time'] = result['generation_time'] + result['execution_time']
        return result

    # ─────────────────────────────────────────────────────────────────────────
    # Database connection helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _get_connection(self):
        """Get or create a PostgreSQL connection."""
        try:
            if self.db_conn and not self.db_conn.closed:
                # Test connection is still alive
                try:
                    self.db_conn.cursor().execute("SELECT 1")
                    return self.db_conn
                except Exception:
                    self.db_conn = None

            self.db_conn = psycopg2.connect(**self.db_config)
            self.db_conn.autocommit = True
            logger.info("✅ DB connected")
            return self.db_conn

        except Exception as e:
            logger.error(f"❌ DB connection failed: {e}")
            self.db_conn = None
            return None

    def _close_connection(self):
        """Close the database connection."""
        if self.db_conn:
            try:
                self.db_conn.close()
            except Exception:
                pass
            self.db_conn = None

    def test_db_connection(self) -> Dict[str, Any]:
        """Test database connection and return table counts."""
        conn = self._get_connection()
        if not conn:
            return {'success': False, 'error': 'Cannot connect to database'}

        try:
            counts = {}
            tables = ['patients', 'providers', 'organizations', 'encounters',
                      'conditions', 'medications', 'procedures', 'payers']
            cur = conn.cursor()
            for t in tables:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM clinical_data.{t}")
                    counts[t] = cur.fetchone()[0]
                except Exception:
                    counts[t] = 'N/A'
            cur.close()
            return {'success': True, 'table_counts': counts}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline usage statistics."""
        total = self.stats['total_queries']
        return {
            'total_queries': total,
            'successful_queries': self.stats['successful_queries'],
            'failed_queries': self.stats['failed_queries'],
            'success_rate': f"{self.stats['successful_queries']/max(total,1)*100:.1f}%",
            'avg_generation_time': (
                f"{self.stats['total_time']/max(self.stats['successful_queries'],1):.2f}s"
            ),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # SQL helpers
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _clean_sql(text: str) -> str:
        """Remove markdown code fences and surrounding whitespace from Gemini output."""
        text = text.strip()
        # Strip ```sql ... ``` or ``` ... ```
        if '```sql' in text:
            text = text.split('```sql', 1)[1].split('```', 1)[0]
        elif '```' in text:
            text = text.split('```', 1)[1].split('```', 1)[0]
        # Strip inline SQL: prefix
        if text.upper().startswith('SQL:'):
            text = text[4:]
        return text.strip()

    @staticmethod
    def _is_valid_sql(sql: str) -> bool:
        """Basic validation: SQL must contain SELECT and FROM."""
        up = sql.upper()
        return 'SELECT' in up and 'FROM' in up

    @staticmethod
    def _add_limit(sql: str, max_rows: int) -> str:
        """Add LIMIT clause if not already present."""
        sql_up = sql.upper().rstrip(';').strip()
        if 'LIMIT' not in sql_up:
            return sql.rstrip(';').strip() + f' LIMIT {max_rows}'
        return sql
