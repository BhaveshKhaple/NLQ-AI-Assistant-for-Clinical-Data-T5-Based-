#!/usr/bin/env python3
import sys, os, json
sys.path.insert(0, 'src')
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

for line in Path('.env').read_text().splitlines():
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        os.environ.setdefault(k.strip(), v.strip())

from nlq.t5_nlq_pipeline import T5NLQPipeline

pipeline = T5NLQPipeline("T5 Clinical (primary)")
pipeline.initialize()

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

results = []
for nlq in failing:
    gen = pipeline.generate_sql(nlq)
    res = {
        'nlq': nlq,
        'sql': gen.get('sql', ''),
        'error': gen.get('error', '')
    }
    
    if gen.get('success'):
        conn = pipeline._get_connection()
        try:
            import pandas as pd
            df = pd.read_sql_query(gen['sql'] + ' LIMIT 5', conn)
            res['db_status'] = 'OK'
            res['db_rows'] = len(df)
        except Exception as e:
            res['db_status'] = 'ERROR'
            res['db_error'] = str(e).strip()
    else:
        res['db_status'] = 'NO_SQL'
        
    results.append(res)
    
Path('tmp_debug_out.json').write_text(json.dumps(results, indent=2))
