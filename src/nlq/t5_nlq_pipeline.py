#!/usr/bin/env python3
"""
T5 NLQ Pipeline
Complete ML flow: Natural Language → T5 Model → SQL → PostgreSQL → Results

Models:
  - t5_clinical_model   (trained on clinical NL→SQL dataset)
  - modetest1           (alternate trained checkpoint)

Input format expected by models:
  "translate to sql: <question> Database Schema: clinical_data\nTables: ..."
"""

import os
import re
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import psycopg2
import pandas as pd

logger = logging.getLogger(__name__)

# ── Schema context appended to every model input ──────────────────────────────
SCHEMA_CONTEXT = (
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

MODELS_ROOT = Path(__file__).parent.parent.parent / "models" / "trained"

AVAILABLE_MODELS = {
    "T5 Clinical (primary)":  str(MODELS_ROOT / "t5_clinical_model"),
    "T5 Clinical (modetest1)": str(MODELS_ROOT / "modetest1"),
}


class T5NLQPipeline:
    """
    Full ML pipeline:
      Natural Language → T5 (local fine-tuned model) → SQL → PostgreSQL → Results
    """

    def __init__(self, model_name: str = "T5 Clinical (primary)"):
        self.model_name = model_name
        self.model_path = AVAILABLE_MODELS.get(model_name, list(AVAILABLE_MODELS.values())[0])
        self.model = None
        self.tokenizer = None
        self.initialized = False

        # DB config from env
        self.db_config = {
            'host':     os.getenv('DB_HOST', 'localhost'),
            'port':     int(os.getenv('DB_PORT', '5432')),
            'database': os.getenv('DB_NAME', 'medical'),
            'user':     os.getenv('DB_USERNAME', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'Pass@123'),
        }
        self.db_conn = None

        self.stats = {'total': 0, 'success': 0, 'failed': 0, 'total_time': 0.0}

    # ── Init ──────────────────────────────────────────────────────────────────

    def initialize(self) -> Dict[str, Any]:
        """Load the T5 model and tokenizer from disk."""
        try:
            from transformers import T5ForConditionalGeneration, AutoTokenizer
            import torch

            logger.info(f"Loading model from: {self.model_path}")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path, local_files_only=True
            )
            self.model = T5ForConditionalGeneration.from_pretrained(
                self.model_path, local_files_only=True
            )
            self.model.eval()

            # Use GPU if available
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            self.model = self.model.to(self.device)

            self.initialized = True
            logger.info(f"✅ Model loaded on {self.device}: {self.model_name}")
            return {
                'success': True,
                'model': self.model_name,
                'device': self.device,
                'path': self.model_path,
            }

        except Exception as e:
            logger.error(f"❌ Model load failed: {e}")
            return {'success': False, 'error': str(e)}

    # ── Core: NL → SQL via T5 ─────────────────────────────────────────────────

    def generate_sql(self, natural_query: str) -> Dict[str, Any]:
        """
        Translate natural language to SQL using the local T5 model.

        Args:
            natural_query: Plain English clinical question

        Returns:
            dict with 'sql', 'success', 'generation_time', 'raw_output', 'error'
        """
        if not self.initialized:
            return {'success': False, 'sql': '', 'error': 'Model not loaded'}

        import torch
        start = time.time()
        self.stats['total'] += 1

        try:
            # Format exactly as training data
            model_input = f"translate to sql: {natural_query} {SCHEMA_CONTEXT}"

            inputs = self.tokenizer(
                model_input,
                return_tensors='pt',
                max_length=512,
                truncation=True,
                padding=True,
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=256,
                    num_beams=4,
                    early_stopping=True,
                    no_repeat_ngram_size=3,
                )

            raw_output = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            generation_time = time.time() - start

            sql = self._clean_sql(raw_output)

            if not self._is_valid_sql(sql):
                self.stats['failed'] += 1
                return {
                    'success': False,
                    'sql': sql,
                    'raw_output': raw_output,
                    'generation_time': generation_time,
                    'error': f'Output does not look like SQL: {sql[:200]}',
                }

            self.stats['success'] += 1
            self.stats['total_time'] += generation_time

            logger.info(f"✅ SQL generated in {generation_time:.2f}s")
            return {
                'success': True,
                'sql': sql,
                'raw_output': raw_output,
                'generation_time': generation_time,
                'model': self.model_name,
                'input': model_input,
            }

        except Exception as e:
            generation_time = time.time() - start
            self.stats['failed'] += 1
            logger.error(f"❌ Generation error: {e}")
            return {
                'success': False,
                'sql': '',
                'raw_output': '',
                'generation_time': generation_time,
                'error': str(e),
            }

    # ── DB Execution ──────────────────────────────────────────────────────────

    def execute_sql(self, sql: str, max_rows: int = 500) -> Dict[str, Any]:
        """Execute SQL against PostgreSQL and return a DataFrame."""
        start = time.time()
        try:
            conn = self._get_connection()
            if not conn:
                return {'success': False, 'data': None,
                        'error': 'Cannot connect to database'}

            sql_limited = self._add_limit(sql, max_rows)
            df = pd.read_sql_query(sql_limited, conn)
            exec_time = time.time() - start

            return {
                'success': True,
                'data': df,
                'row_count': len(df),
                'execution_time': exec_time,
                'sql_executed': sql_limited,
            }

        except Exception as e:
            self._close_connection()
            return {
                'success': False,
                'data': None,
                'row_count': 0,
                'execution_time': time.time() - start,
                'error': str(e),
            }

    def run_query(self, natural_query: str, execute: bool = True) -> Dict[str, Any]:
        """Full pipeline: NL → Model → SQL → (optionally) DB → Results."""
        result = {
            'natural_query': natural_query,
            'success': False,
            'sql': '',
            'raw_output': '',
            'data': None,
            'generation_time': 0.0,
            'execution_time': 0.0,
            'total_time': 0.0,
            'row_count': 0,
            'error': None,
        }

        gen = self.generate_sql(natural_query)
        result['sql'] = gen.get('sql', '')
        result['raw_output'] = gen.get('raw_output', '')
        result['generation_time'] = gen.get('generation_time', 0.0)
        result['model_input'] = gen.get('input', '')

        if not gen['success']:
            result['error'] = gen.get('error')
            return result

        if execute:
            ex = self.execute_sql(gen['sql'])
            result['data'] = ex.get('data')
            result['execution_time'] = ex.get('execution_time', 0.0)
            result['row_count'] = ex.get('row_count', 0)
            if not ex['success']:
                result['error'] = ex.get('error')
                result['total_time'] = result['generation_time'] + result['execution_time']
                return result

        result['success'] = True
        result['total_time'] = result['generation_time'] + result['execution_time']
        return result

    # ── DB helpers ────────────────────────────────────────────────────────────

    def _get_connection(self):
        try:
            if self.db_conn and not self.db_conn.closed:
                self.db_conn.cursor().execute("SELECT 1")
                return self.db_conn
        except Exception:
            self.db_conn = None

        try:
            self.db_conn = psycopg2.connect(**self.db_config)
            self.db_conn.autocommit = True
            return self.db_conn
        except Exception as e:
            logger.error(f"DB connect failed: {e}")
            return None

    def _close_connection(self):
        if self.db_conn:
            try:
                self.db_conn.close()
            except Exception:
                pass
            self.db_conn = None

    def test_db_connection(self) -> Dict[str, Any]:
        conn = self._get_connection()
        if not conn:
            return {'success': False, 'error': 'Cannot connect to database'}
        try:
            counts = {}
            cur = conn.cursor()
            for t in ['patients', 'providers', 'organizations', 'encounters',
                      'conditions', 'medications', 'procedures', 'immunizations']:
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
        t = self.stats['total']
        s = self.stats['success']
        return {
            'total_queries': t,
            'successful': s,
            'failed': self.stats['failed'],
            'success_rate': f"{s/max(t,1)*100:.1f}%",
            'avg_gen_time': f"{self.stats['total_time']/max(s,1):.2f}s",
        }

    # ── SQL helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _clean_sql(text: str) -> str:
        text = text.strip()
        if '```sql' in text:
            text = text.split('```sql', 1)[1].split('```', 1)[0]
        elif '```' in text:
            text = text.split('```', 1)[1].split('```', 1)[0]
        return text.strip()

    @staticmethod
    def _is_valid_sql(sql: str) -> bool:
        up = sql.upper()
        return 'SELECT' in up and 'FROM' in up

    @staticmethod
    def _add_limit(sql: str, n: int) -> str:
        if 'LIMIT' not in sql.upper():
            return sql.rstrip(';').strip() + f' LIMIT {n}'
        return sql
