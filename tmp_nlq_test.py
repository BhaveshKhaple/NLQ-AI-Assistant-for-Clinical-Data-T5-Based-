#!/usr/bin/env python3
"""
NLQ Smoke Test
Runs a wide set of natural language queries through the T5 model + PostgreSQL
and prints a clear pass/fail report with actual row counts.
"""
import sys, os
sys.path.insert(0, 'src')
from pathlib import Path

# Load .env
for line in Path('.env').read_text().splitlines():
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        os.environ.setdefault(k.strip(), v.strip())

from nlq.t5_nlq_pipeline import T5NLQPipeline
import time

TEST_QUERIES = [
    # ── counts ──────────────────────────────────────────────────────────────
    "How many patients do we have?",
    "How many providers are in the system?",
    "How many encounters have been recorded?",
    "How many organizations are registered?",
    "How many different medications are prescribed?",
    # ── demographics ─────────────────────────────────────────────────────────
    "Show all male patients",
    "List female patients",
    "What is the gender distribution of our patients?",
    # ── conditions ───────────────────────────────────────────────────────────
    "Find patients with diabetes",
    "Show patients diagnosed with hypertension",
    "What are the 10 most common medical conditions?",
    "Find patients with asthma",
    "List patients with COPD",
    # ── medications ──────────────────────────────────────────────────────────
    "What are the most frequently prescribed medications?",
    "Which patients are taking Metformin?",
    "Show top 10 medications by prescription count",
    # ── providers ────────────────────────────────────────────────────────────
    "List all Cardiology specialists",
    "Show providers in California",
    "List all specialties",
    # ── geography ────────────────────────────────────────────────────────────
    "List patients in Texas",
    "Show patients from Massachusetts",
    "Get organizations in NY state",
    # ── age ──────────────────────────────────────────────────────────────────
    "Find patients older than 65",
    "Show patients under 18 years old",
    # ── encounters ───────────────────────────────────────────────────────────
    "Show encounters from the last 6 months",
    "Show recent encounters",
    # ── costs ────────────────────────────────────────────────────────────────
    "Find patients with healthcare expenses over $50,000",
    "Show patients by income",
    # ── comorbidities ─────────────────────────────────────────────────────────
    "Find patients with both Diabetes and Hypertension",
    "Show patients on 4 or more medications",
]

print("\n" + "="*70)
print("  NLQ Model + Database Smoke Test")
print("  Model: T5 Clinical (primary)")
print("="*70)

pipeline = T5NLQPipeline("T5 Clinical (primary)")
r = pipeline.initialize()
if not r['success']:
    print(f"❌ Model failed to load: {r['error']}")
    sys.exit(1)
print(f"✅ Model loaded on {r['device']}\n")

results = []
for nlq in TEST_QUERIES:
    t0 = time.time()
    res = pipeline.run_query(nlq, execute=True)
    elapsed = time.time() - t0

    sql = res.get('sql', '').strip().replace('\n', ' ')
    # Truncate long SQL for display
    sql_display = (sql[:90] + '…') if len(sql) > 90 else sql

    if res['success']:
        rows = res.get('row_count', 0)
        status = "✅ PASS"
        detail = f"{rows} row(s)"
    elif res.get('sql'):
        status = "⚠️  SQL OK / DB ERR"
        detail = str(res.get('error', ''))[:60]
    else:
        status = "❌ FAIL"
        detail = str(res.get('error', ''))[:60]

    results.append({
        'nlq': nlq,
        'status': status,
        'rows': res.get('row_count', 0),
        'gen_t': res.get('generation_time', 0),
        'sql': sql_display,
        'detail': detail,
    })

    print(f"{status}  [{elapsed:.1f}s]  {nlq}")
    print(f"         SQL: {sql_display}")
    print(f"         Result: {detail}")
    print()

# Summary
passed  = [r for r in results if '✅' in r['status']]
warned  = [r for r in results if '⚠️' in r['status']]
failed  = [r for r in results if '❌' in r['status']]

print("="*70)
print(f"  SUMMARY: {len(passed)} passed | {len(warned)} SQL-OK-but-DB-error | {len(failed)} failed | {len(results)} total")
print("="*70)

print("\n\n── WORKING QUERIES (model + DB) ──────────────────────────────────────")
for r in passed:
    print(f"  ✅  {r['nlq']}  →  {r['rows']} row(s)")

if warned:
    print("\n── SQL GENERATED BUT DB ERROR ────────────────────────────────────────")
    for r in warned:
        print(f"  ⚠️   {r['nlq']}")
        print(f"       {r['detail']}")

if failed:
    print("\n── FAILED (no SQL) ───────────────────────────────────────────────────")
    for r in failed:
        print(f"  ❌  {r['nlq']}")
        print(f"       {r['detail']}")
