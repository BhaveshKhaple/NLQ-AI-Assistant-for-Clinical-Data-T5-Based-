#!/usr/bin/env python3
"""
Debug script - find exact DB errors for failing queries
"""
import sys, os
sys.path.insert(0, 'src')
from pathlib import Path
for line in Path('.env').read_text().splitlines():
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        os.environ.setdefault(k.strip(), v.strip())

from nlq.t5_nlq_pipeline import T5NLQPipeline
import psycopg2

pipeline = T5NLQPipeline("T5 Clinical (primary)")
pipeline.initialize()

# Try the failing queries and get the FULL error + the actual SQL
failing = [
    "Find patients with diabetes",
    "Which patients are taking Metformin?",
    "List patients in Texas",
    "Show encounters from the last 6 months",
    "What are the most frequently prescribed medications?",
    "Find patients with both Diabetes and Hypertension",
    "Show patients on 4 or more medications",
    "Find patients with healthcare expenses over $50,000",
]

for nlq in failing:
    gen = pipeline.generate_sql(nlq)
    print(f"\nNLQ: {nlq}")
    print(f"SQL: {gen['sql']}")
    if gen['success']:
        conn = pipeline._get_connection()
        try:
            import pandas as pd
            df = pd.read_sql_query(gen['sql'] + ' LIMIT 5', conn)
            print(f"OK: {len(df)} rows")
        except Exception as e:
            print(f"ERROR: {e}")
    print()
