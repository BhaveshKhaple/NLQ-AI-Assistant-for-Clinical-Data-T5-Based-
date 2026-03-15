#!/usr/bin/env python3
"""
Clinical NLQ Assistant — ML Project Demo
Flow: Natural Language → T5 Model → Generated SQL → PostgreSQL → Results
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

import streamlit as st
import pandas as pd

# ── Path & env setup ──────────────────────────────────────────────────────────
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

_env = Path(__file__).parent.parent.parent / ".env"
if _env.exists():
    for line in _env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from nlq.t5_nlq_pipeline import T5NLQPipeline, AVAILABLE_MODELS

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Clinical NLQ — ML Demo",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* { font-family: 'Inter', sans-serif; }

/* ── Pipeline flow ── */
.pipeline {
    display: flex;
    align-items: stretch;
    gap: 0;
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #e0e7ff;
    margin-bottom: 28px;
}
.pipe-step {
    flex: 1;
    padding: 16px 10px;
    text-align: center;
    position: relative;
}
.pipe-step .icon { font-size: 1.6rem; margin-bottom: 4px; }
.pipe-step .label { font-size: 0.72rem; font-weight: 600; text-transform: uppercase;
                    letter-spacing: 0.05em; opacity: 0.7; }
.pipe-step .name  { font-size: 0.9rem; font-weight: 700; margin-top: 2px; }
.pipe-step.s1 { background: #eff6ff; color: #1d4ed8; }
.pipe-step.s2 { background: #f5f3ff; color: #6d28d9; }
.pipe-step.s3 { background: #faf5ff; color: #7c3aed; }
.pipe-step.s4 { background: #ecfdf5; color: #065f46; }
.pipe-step.s5 { background: #f0fdf4; color: #166534; }
.pipe-arrow {
    display: flex; align-items: center; justify-content: center;
    background: #f8fafc; padding: 0 6px; color: #94a3b8;
    font-size: 1.1rem; font-weight: bold;
}

/* ── Hero ── */
.hero {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 60%, #2563eb 100%);
    border-radius: 14px;
    padding: 30px 36px;
    margin-bottom: 28px;
    color: white;
}
.hero h1 { font-size: 1.9rem; margin: 0 0 4px; font-weight: 700; }
.hero p  { font-size: 0.97rem; opacity: 0.85; margin: 0; }
.badge {
    display: inline-block;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.77rem;
    margin: 8px 4px 0 0;
}

/* ── SQL output ── */
.sql-box {
    background: #0f172a;
    border-left: 4px solid #6d28d9;
    border-radius: 8px;
    padding: 18px 22px;
    font-family: 'Courier New', monospace;
    font-size: 0.87rem;
    color: #e2e8f0;
    white-space: pre-wrap;
    overflow-x: auto;
    line-height: 1.55;
}

/* ── Model input box ── */
.model-input-box {
    background: #faf5ff;
    border-left: 4px solid #a78bfa;
    border-radius: 8px;
    padding: 14px 18px;
    font-family: 'Courier New', monospace;
    font-size: 0.8rem;
    color: #3b0764;
    white-space: pre-wrap;
    overflow-wrap: break-word;
    line-height: 1.5;
}

/* ── Cards ── */
.stat-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px 18px;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

/* ── History ── */
.hist {
    border-left: 3px solid #818cf8;
    padding: 6px 10px;
    margin-bottom: 5px;
    font-size: 0.8rem;
    color: #374151;
    background: #f8faff;
    border-radius: 0 6px 6px 0;
}
.hist.fail { border-left-color: #f87171; background: #fff5f5; }

/* ── Step highlight ── */
.step-header {
    font-size: 0.82rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #6d28d9;
    margin: 22px 0 6px;
}
.step-result-header {
    font-size: 0.82rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #065f46;
    margin: 22px 0 6px;
}

/* ── Explorer ── */
.table-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #6366f1;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 8px;
    cursor: pointer;
    transition: box-shadow 0.15s;
}
.table-card:hover { box-shadow: 0 4px 12px rgba(99,102,241,0.15); }
.table-card .tname { font-weight: 700; color: #3730a3; font-size: 0.9rem; }
.table-card .tcount { font-size: 0.78rem; color: #6b7280; margin-top: 2px; }
.schema-row {
    display: flex; gap: 10px; align-items: baseline;
    padding: 5px 0; border-bottom: 1px solid #f1f5f9; font-size: 0.83rem;
}
.schema-col { font-weight: 600; color: #1e293b; min-width: 160px; }
.schema-type { color: #6366f1; font-family: monospace; font-size: 0.81rem; }
.schema-fk { color: #0891b2; font-size: 0.76rem; margin-left: 6px; }
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
def _init():
    defaults = {
        'pipeline': None,
        'model_name': list(AVAILABLE_MODELS.keys())[0],
        'loaded_model_name': None,
        'history': [],
        'preset': '',
        'db_counts': {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()


# ── Pipeline cache ─────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def _load_pipeline(model_name: str):
    p = T5NLQPipeline(model_name=model_name)
    result = p.initialize()
    return p, result


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
def render_sidebar():
    with st.sidebar:
        st.markdown("## 🤖 Model")

        chosen = st.selectbox(
            "Select trained model",
            options=list(AVAILABLE_MODELS.keys()),
            index=list(AVAILABLE_MODELS.keys()).index(st.session_state.model_name),
        )
        if chosen != st.session_state.model_name:
            st.session_state.model_name = chosen
            st.rerun()

        pipeline, init_result = _load_pipeline(st.session_state.model_name)

        if init_result.get('success'):
            st.success(f"✅ **{st.session_state.model_name}**")
            device = init_result.get('device', 'cpu')
            st.caption(f"Running on: **{device.upper()}**")
        else:
            st.error(f"❌ {init_result.get('error','Load failed')}")

        st.divider()

        # DB
        st.markdown("## 🗄️ Database")
        if st.button("Connect & Count Rows", use_container_width=True):
            dbr = pipeline.test_db_connection()
            if dbr['success']:
                st.session_state.db_counts = dbr['table_counts']
                st.success("PostgreSQL connected")
            else:
                st.error(dbr['error'])

        if st.session_state.db_counts:
            for t, c in st.session_state.db_counts.items():
                cnt = f"{c:,}" if isinstance(c, int) else str(c)
                st.markdown(f"<small>• `{t}`: **{cnt}**</small>", unsafe_allow_html=True)

        st.divider()

        # Session stats
        st.markdown("## 📊 Session")
        stats = pipeline.get_stats() if init_result.get('success') else {}
        c1, c2 = st.columns(2)
        c1.metric("Queries", stats.get('total_queries', 0))
        c2.metric("Success", stats.get('success_rate', '—'))
        st.caption(f"Avg generation: {stats.get('avg_gen_time','—')}")

        st.divider()

        # History
        st.markdown("## 🕐 History")
        if st.session_state.history:
            for h in reversed(st.session_state.history[-12:]):
                cls = "hist" if h['success'] else "hist fail"
                icon = "✅" if h['success'] else "❌"
                ts = h['ts'].strftime('%H:%M:%S')
                st.markdown(
                    f'<div class="{cls}">{icon} <b>{ts}</b><br>'
                    f'{h["nlq"][:55]}{"…" if len(h["nlq"])>55 else ""}</div>',
                    unsafe_allow_html=True
                )
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.history = []
                st.rerun()

    return pipeline, init_result


# ══════════════════════════════════════════════════════════════════════════════
# NLQ TAB
# ══════════════════════════════════════════════════════════════════════════════
def render_nlq_tab(pipeline, init_ok):
    """NLQ pipeline tab content."""
    # Examples
    st.markdown("**💡 Try these examples:**")
    examples = [
        ("👥 Patient Count",     "How many patients do we have?"),
        ("💊 Diabetes",          "Find patients with diabetes"),
        ("🏥 CA Providers",      "Show providers in California"),
        ("🩺 Top Conditions",    "What are the 10 most common medical conditions?"),
        ("👨‍⚕️ Cardiologists",    "List all Cardiology specialists"),
        ("💊 Metformin",         "Which patients are taking Metformin?"),
        ("📍 Texas Patients",    "List patients in Texas"),
        ("💰 High-Cost",         "Find patients with healthcare expenses over $50,000"),
        ("⚠️ Comorbidities",     "Find patients with both Diabetes and Hypertension"),
        ("📅 Recent Encounters", "Show encounters from the last 6 months"),
    ]
    cols = st.columns(5)
    for i, (label, query) in enumerate(examples):
        if cols[i % 5].button(label, use_container_width=True, key=f"ex_{i}"):
            st.session_state.preset = query
            st.rerun()

    st.divider()

    # ── Query Input ────────────────────────────────────────────────────────────
    preset = st.session_state.preset
    st.session_state.preset = ''

    col_q, col_opt = st.columns([5, 1])
    with col_q:
        user_nlq = st.text_area(
            "**🔍 Enter your clinical question:**",
            value=preset,
            height=90,
            placeholder="e.g. How many patients do we have?",
        )
    with col_opt:
        st.markdown("<br>", unsafe_allow_html=True)
        run_db = st.checkbox("Execute SQL", value=True,
                             help="Run the generated SQL against the database")
        run_btn = st.button("▶ Run", type="primary", use_container_width=True)

    # ── Process ───────────────────────────────────────────────────────────────
    if run_btn:
        nlq = user_nlq.strip()
        if not nlq:
            st.warning("Please enter a question first.")
            return

        with st.spinner(f"🤖 Running through {st.session_state.model_name}..."):
            result = pipeline.run_query(nlq, execute=run_db)

        st.session_state.history.append({
            'nlq': nlq,
            'success': result['success'],
            'sql': result.get('sql', ''),
            'ts': datetime.now(),
        })

        # ── STEP 1: Model input ───────────────────────────────────────────────
        with st.expander("🔎 Step 1 — Model Input (what was sent to T5)", expanded=False):
            st.markdown('<div class="step-header">Model Input String</div>', unsafe_allow_html=True)
            model_input = result.get('model_input', f"translate to sql: {nlq} Database Schema: clinical_data\n...")
            st.markdown(f'<div class="model-input-box">{model_input}</div>', unsafe_allow_html=True)

        # ── STEP 2: Generated SQL ─────────────────────────────────────────────
        st.markdown('<div class="step-header">Step 2 — Model Output: Generated SQL</div>',
                    unsafe_allow_html=True)

        if result.get('sql'):
            st.markdown(f'<div class="sql-box">{result["sql"]}</div>', unsafe_allow_html=True)

            # Timings
            m1, m2, m3 = st.columns(3)
            m1.metric("⚡ Generation Time", f"{result['generation_time']:.2f}s")
            m2.metric("🤖 Model", st.session_state.model_name.split()[0])
            if run_db:
                m3.metric("🗃️ DB Execution Time", f"{result['execution_time']:.3f}s")
        else:
            st.error(f"❌ The model did not produce valid SQL.\n\nError: {result.get('error','Unknown error')}")
            return

        # ── STEP 3: DB Results ────────────────────────────────────────────────
        if run_db:
            st.markdown('<div class="step-result-header">Step 3 — Database Search Results</div>',
                        unsafe_allow_html=True)

            if not result['success']:
                st.error(f"❌ DB Error: {result.get('error','')}")
                st.info("The SQL above may need to be adjusted. "
                        "The T5 model's output is shown above exactly as generated.")
            else:
                df = result.get('data')
                if df is None or len(df) == 0:
                    st.info("✅ Query executed — no rows returned.")
                else:
                    st.success(f"✅ **{len(df):,} rows** returned in {result['total_time']:.2f}s total")
                    st.dataframe(df, use_container_width=True, height=400)

                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    dl1, dl2, _ = st.columns([1, 1, 4])
                    dl1.download_button("📥 CSV",
                                        data=df.to_csv(index=False),
                                        file_name=f"nlq_result_{ts}.csv",
                                        mime="text/csv")
                    dl2.download_button("📥 JSON",
                                        data=df.to_json(orient='records', indent=2),
                                        file_name=f"nlq_result_{ts}.json",
                                        mime="application/json")

    # ── About ─────────────────────────────────────────────────────────────────
    with st.expander("ℹ️ About this Project"):
        st.markdown("""
        **Clinical NLQ — ML Project**

        | Component | Detail |
        |-----------|--------|
        | **Task** | Natural Language → SQL for clinical data |
        | **ML Models** | T5 Transformer (fine-tuned locally) |
        | **Training Data** | 6,549 NL→SQL pairs (`train/val/test_data.json`) |
        | **Database** | PostgreSQL · `medical.clinical_data` |
        | **Data Source** | Synthea Synthetic Patient Generator |
        | **Tables** | 13 clinical tables |
        | **Inference** | 100% local — no external API |

        **Pipeline Steps:**
        1. User enters a natural language clinical question
        2. The question is formatted and fed to the fine-tuned T5 model
        3. T5 generates a PostgreSQL SELECT statement
        4. The SQL executes against the clinical database
        5. Results display in the app

        **Models available:**
        - `t5_clinical_model` — primary trained checkpoint
        - `modetest1` — alternate training checkpoint
        """)


# ══════════════════════════════════════════════════════════════════════════════
# DATABASE EXPLORER
# ══════════════════════════════════════════════════════════════════════════════

DB_TABLES = [
    'patients', 'providers', 'organizations', 'encounters',
    'conditions', 'medications', 'procedures', 'observations',
    'allergies', 'care_plans', 'immunizations', 'claims', 'payers',
]

# Column descriptions for schema display
TABLE_SCHEMAS = {
    'patients': [
        ('id', 'UUID', 'Primary Key'),
        ('birth_date', 'DATE', ''),
        ('death_date', 'DATE', ''),
        ('first_name', 'VARCHAR', ''),
        ('last_name', 'VARCHAR', ''),
        ('gender', 'CHAR(1)', "'M' or 'F'"),
        ('race', 'VARCHAR', ''),
        ('ethnicity', 'VARCHAR', ''),
        ('city', 'VARCHAR', ''),
        ('state', 'CHAR(2)', ''),
        ('zip', 'VARCHAR', ''),
        ('marital_status', 'VARCHAR', ''),
        ('healthcare_expenses', 'DECIMAL', ''),
        ('healthcare_coverage', 'DECIMAL', ''),
        ('income', 'DECIMAL', ''),
    ],
    'providers': [
        ('id', 'UUID', 'Primary Key'),
        ('organization_id', 'UUID', 'FK → organizations'),
        ('name', 'VARCHAR', ''),
        ('gender', 'CHAR(1)', ''),
        ('speciality', 'VARCHAR', ''),
        ('city', 'VARCHAR', ''),
        ('state', 'CHAR(2)', ''),
        ('zip', 'VARCHAR', ''),
        ('utilization', 'INTEGER', ''),
    ],
    'organizations': [
        ('id', 'UUID', 'Primary Key'),
        ('name', 'VARCHAR', ''),
        ('city', 'VARCHAR', ''),
        ('state', 'CHAR(2)', ''),
        ('zip', 'VARCHAR', ''),
        ('phone', 'VARCHAR', ''),
        ('revenue', 'DECIMAL', ''),
        ('utilization', 'INTEGER', ''),
    ],
    'encounters': [
        ('id', 'UUID', 'Primary Key'),
        ('start_time', 'TIMESTAMP', ''),
        ('stop_time', 'TIMESTAMP', ''),
        ('patient_id', 'UUID', 'FK → patients'),
        ('organization_id', 'UUID', 'FK → organizations'),
        ('provider_id', 'UUID', 'FK → providers'),
        ('payer_id', 'UUID', 'FK → payers'),
        ('encounter_class', 'VARCHAR', ''),
        ('description', 'TEXT', ''),
        ('base_encounter_cost', 'DECIMAL', ''),
        ('total_claim_cost', 'DECIMAL', ''),
        ('payer_coverage', 'DECIMAL', ''),
        ('reason_description', 'TEXT', ''),
    ],
    'conditions': [
        ('id', 'UUID', 'Primary Key'),
        ('start_date', 'DATE', ''),
        ('stop_date', 'DATE', 'NULL = active'),
        ('patient_id', 'UUID', 'FK → patients'),
        ('encounter_id', 'UUID', 'FK → encounters'),
        ('code', 'VARCHAR', 'SNOMED code'),
        ('description', 'TEXT', ''),
    ],
    'medications': [
        ('id', 'UUID', 'Primary Key'),
        ('start_date', 'DATE', ''),
        ('stop_date', 'DATE', 'NULL = active'),
        ('patient_id', 'UUID', 'FK → patients'),
        ('encounter_id', 'UUID', 'FK → encounters'),
        ('payer_id', 'UUID', 'FK → payers'),
        ('code', 'VARCHAR', 'RxNorm code'),
        ('description', 'TEXT', ''),
        ('base_cost', 'DECIMAL', ''),
        ('total_cost', 'DECIMAL', ''),
        ('reason_description', 'TEXT', ''),
    ],
    'procedures': [
        ('id', 'UUID', 'Primary Key'), ('date', 'DATE', ''),
        ('patient_id', 'UUID', 'FK → patients'), ('encounter_id', 'UUID', 'FK → encounters'),
        ('code', 'VARCHAR', ''), ('description', 'TEXT', ''), ('base_cost', 'DECIMAL', ''),
        ('reason_description', 'TEXT', ''),
    ],
    'observations': [
        ('id', 'UUID', 'Primary Key'), ('date', 'DATE', ''),
        ('patient_id', 'UUID', 'FK → patients'), ('encounter_id', 'UUID', 'FK → encounters'),
        ('category', 'VARCHAR', ''), ('code', 'VARCHAR', ''),
        ('description', 'TEXT', ''), ('value', 'VARCHAR', ''), ('units', 'VARCHAR', ''),
    ],
    'allergies': [
        ('id', 'UUID', 'Primary Key'), ('start_date', 'DATE', ''), ('stop_date', 'DATE', ''),
        ('patient_id', 'UUID', 'FK → patients'), ('encounter_id', 'UUID', 'FK → encounters'),
        ('code', 'VARCHAR', ''), ('category', 'VARCHAR', ''),
        ('description1', 'TEXT', ''), ('severity1', 'VARCHAR', ''),
    ],
    'care_plans': [
        ('id', 'UUID', 'Primary Key'), ('start_date', 'DATE', ''), ('stop_date', 'DATE', ''),
        ('patient_id', 'UUID', 'FK → patients'), ('encounter_id', 'UUID', 'FK → encounters'),
        ('code', 'VARCHAR', ''), ('description', 'TEXT', ''), ('reason_description', 'TEXT', ''),
    ],
    'immunizations': [
        ('id', 'UUID', 'Primary Key'), ('date', 'DATE', ''),
        ('patient_id', 'UUID', 'FK → patients'), ('encounter_id', 'UUID', 'FK → encounters'),
        ('code', 'VARCHAR', ''), ('description', 'TEXT', ''), ('base_cost', 'DECIMAL', ''),
    ],
    'claims': [
        ('id', 'UUID', 'Primary Key'), ('patient_id', 'UUID', 'FK → patients'),
        ('provider_id', 'UUID', 'FK → providers'), ('service_date', 'DATE', ''),
        ('diagnosis1', 'VARCHAR', ''), ('diagnosis2', 'VARCHAR', ''),
    ],
    'payers': [
        ('id', 'UUID', 'Primary Key'), ('name', 'VARCHAR', ''),
        ('ownership', 'VARCHAR', ''), ('city', 'VARCHAR', ''), ('state', 'CHAR(2)', ''),
        ('amount_covered', 'DECIMAL', ''), ('amount_uncovered', 'DECIMAL', ''),
        ('revenue', 'DECIMAL', ''), ('covered_encounters', 'INTEGER', ''),
        ('covered_medications', 'INTEGER', ''), ('unique_customers', 'INTEGER', ''),
    ],
}


def _db_query(pipeline, sql: str, params=None):
    """Run a query using the pipeline's DB connection and return a DataFrame."""
    conn = pipeline._get_connection()
    if not conn:
        return None, 'Cannot connect to database'
    try:
        import psycopg2.extras
        df = pd.read_sql_query(sql, conn)
        return df, None
    except Exception as e:
        return None, str(e)


def render_db_explorer(pipeline: T5NLQPipeline):
    """Full database explorer tab."""

    st.markdown("### 🗄️ Database Explorer")
    st.caption("`medical.clinical_data` PostgreSQL schema · Synthea synthetic clinical data")

    # ── Sub-tabs inside explorer ───────────────────────────────────────────────
    et1, et2, et3 = st.tabs(["📋 Browse Tables", "🔬 Schema", "⚡ Custom SQL"])

    # ── Tab 1: Browse Tables ───────────────────────────────────────────────────
    with et1:
        col_left, col_right = st.columns([1, 2], gap="large")

        with col_left:
            st.markdown("**Select a table:**")
            selected = st.radio(
                "Tables",
                DB_TABLES,
                label_visibility="collapsed",
                key="explorer_table",
            )

        with col_right:
            if selected:
                # Row count
                cnt_df, err = _db_query(
                    pipeline,
                    f"SELECT COUNT(*) as total FROM clinical_data.{selected}"
                )
                row_count = int(cnt_df.iloc[0]['total']) if cnt_df is not None else '?'

                st.markdown(f"#### `clinical_data.{selected}`")
                c1, c2 = st.columns(2)
                c1.metric("Total Rows", f"{row_count:,}" if isinstance(row_count, int) else row_count)
                cols_count = len(TABLE_SCHEMAS.get(selected, []))
                c2.metric("Columns", cols_count)

                # Sample rows
                n_rows = st.slider("Sample rows", 5, 100, 20, key="sample_n")
                sample_df, err = _db_query(
                    pipeline,
                    f"SELECT * FROM clinical_data.{selected} LIMIT {n_rows}"
                )
                if err:
                    st.error(f"❌ {err}")
                elif sample_df is not None:
                    st.dataframe(sample_df, use_container_width=True, height=380)
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    st.download_button(
                        f"📥 Download {selected} sample",
                        data=sample_df.to_csv(index=False),
                        file_name=f"{selected}_sample_{ts}.csv",
                        mime="text/csv",
                    )

    # ── Tab 2: Schema ──────────────────────────────────────────────────────────
    with et2:
        st.markdown("**Database schema overview — all 13 clinical tables:**")

        # Overview table counts
        with st.spinner("Loading table counts…"):
            rows = []
            for t in DB_TABLES:
                df, _ = _db_query(pipeline, f"SELECT COUNT(*) as n FROM clinical_data.{t}")
                cnt = int(df.iloc[0]['n']) if df is not None else 0
                cols = len(TABLE_SCHEMAS.get(t, []))
                rows.append({'Table': t, 'Rows': f"{cnt:,}", 'Columns': cols})
            summary_df = pd.DataFrame(rows)
        st.dataframe(summary_df, use_container_width=True, hide_index=True, height=380)

        st.markdown("---")
        st.markdown("**Detailed column definitions:**")
        tbl_sel = st.selectbox(
            "Choose a table to view column definitions",
            DB_TABLES,
            key="schema_table_sel",
        )
        if tbl_sel and tbl_sel in TABLE_SCHEMAS:
            schema_rows = []
            for col, dtype, note in TABLE_SCHEMAS[tbl_sel]:
                schema_rows.append({
                    'Column': col,
                    'Type': dtype,
                    'Notes': note,
                })
            st.dataframe(
                pd.DataFrame(schema_rows),
                use_container_width=True,
                hide_index=True,
                height=min(40 + len(schema_rows) * 36, 500),
            )

        # ERD summary
        with st.expander("📌 Key Foreign Key Relationships"):
            st.markdown("""
            | Child Column | → | Parent Table |
            |---|---|---|
            | `encounters.patient_id` | → | `patients.id` |
            | `encounters.provider_id` | → | `providers.id` |
            | `encounters.organization_id` | → | `organizations.id` |
            | `encounters.payer_id` | → | `payers.id` |
            | `providers.organization_id` | → | `organizations.id` |
            | `conditions.encounter_id` | → | `encounters.id` |
            | `medications.encounter_id` | → | `encounters.id` |
            | `procedures.encounter_id` | → | `encounters.id` |
            | `observations.encounter_id` | → | `encounters.id` |
            | `immunizations.encounter_id` | → | `encounters.id` |
            | `allergies.encounter_id` | → | `encounters.id` |
            | `claims.patient_id` | → | `patients.id` |
            | `claims.provider_id` | → | `providers.id` |
            """)

    # ── Tab 3: Custom SQL ──────────────────────────────────────────────────────
    with et3:
        st.markdown("**Run your own SQL against the database:**")
        st.caption("⚠️ Read-only — only SELECT queries are permitted.")

        quick_sqls = {
            "Patient count by gender": "SELECT gender, COUNT(*) as count FROM clinical_data.patients GROUP BY gender ORDER BY count DESC",
            "Top 10 conditions": "SELECT description, COUNT(*) as count FROM clinical_data.conditions GROUP BY description ORDER BY count DESC LIMIT 10",
            "Top 10 medications": "SELECT description, COUNT(*) as count FROM clinical_data.medications GROUP BY description ORDER BY count DESC LIMIT 10",
            "Providers by specialty": "SELECT speciality, COUNT(*) as count FROM clinical_data.providers GROUP BY speciality ORDER BY count DESC",
            "Encounter class distribution": "SELECT encounter_class, COUNT(*) as count FROM clinical_data.encounters GROUP BY encounter_class ORDER BY count DESC",
            "Average patient age": "SELECT ROUND(AVG(EXTRACT(YEAR FROM AGE(birth_date)))) as avg_age FROM clinical_data.patients WHERE death_date IS NULL",
            "Patients by state": "SELECT state, COUNT(*) as count FROM clinical_data.patients GROUP BY state ORDER BY count DESC",
            "Payer coverage overview": "SELECT name, amount_covered, amount_uncovered, unique_customers FROM clinical_data.payers ORDER BY unique_customers DESC",
        }

        chosen_quick = st.selectbox(
            "Quick queries (optional):",
            ['— type your own below —'] + list(quick_sqls.keys()),
            key="quick_sql_sel",
        )

        default_sql = quick_sqls.get(chosen_quick, "SELECT * FROM clinical_data.patients LIMIT 10")

        custom_sql = st.text_area(
            "SQL Query:",
            value=default_sql,
            height=120,
            key="custom_sql_input",
        )

        if st.button("▶ Execute", type="primary", key="exec_custom_sql"):
            sql = custom_sql.strip()
            if not sql:
                st.warning("Enter a SQL query first.")
            elif not sql.upper().lstrip().startswith('SELECT'):
                st.error("Only SELECT queries are allowed.")
            else:
                with st.spinner("Running query…"):
                    t0 = time.time()
                    df, err = _db_query(pipeline, sql)
                    elapsed = time.time() - t0
                if err:
                    st.error(f"❌ {err}")
                elif df is not None:
                    st.success(f"✅ {len(df):,} rows in {elapsed:.3f}s")
                    st.dataframe(df, use_container_width=True, height=400)
                    ts_s = datetime.now().strftime('%Y%m%d_%H%M%S')
                    dl1, dl2, _ = st.columns([1, 1, 4])
                    dl1.download_button("📥 CSV",
                                        data=df.to_csv(index=False),
                                        file_name=f"custom_query_{ts_s}.csv",
                                        mime="text/csv",
                                        key="dl_csv_custom")
                    dl2.download_button("📥 JSON",
                                        data=df.to_json(orient='records', indent=2),
                                        file_name=f"custom_query_{ts_s}.json",
                                        mime="application/json",
                                        key="dl_json_custom")


# ── Entry ─────────────────────────────────────────────────────────────────────
def main():
    pipeline, init_result = render_sidebar()
    init_ok = init_result.get('success', False)

    # Hero + flow always visible
    st.markdown("""
    <div class="hero">
        <h1>🏥 Clinical NLQ Assistant</h1>
        <p>Master's Project · Clinical Natural Language Query using Fine-tuned T5 Transformer</p>
        <span class="badge">📊 Synthea Data</span>
        <span class="badge">🤗 T5 Fine-tuned</span>
        <span class="badge">🗃️ PostgreSQL</span>
        <span class="badge">⚡ Local Inference</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="pipeline">
        <div class="pipe-step s1"><div class="icon">📝</div><div class="label">Input</div><div class="name">Natural Language</div></div>
        <div class="pipe-arrow">→</div>
        <div class="pipe-step s2"><div class="icon">🤖</div><div class="label">ML Model</div><div class="name">T5 Transformer</div></div>
        <div class="pipe-arrow">→</div>
        <div class="pipe-step s3"><div class="icon">📋</div><div class="label">Output</div><div class="name">Generated SQL</div></div>
        <div class="pipe-arrow">→</div>
        <div class="pipe-step s4"><div class="icon">🗃️</div><div class="label">Database</div><div class="name">PostgreSQL</div></div>
        <div class="pipe-arrow">→</div>
        <div class="pipe-step s5"><div class="icon">📊</div><div class="label">Output</div><div class="name">Results</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Tabs
    tab_nlq, tab_explorer = st.tabs(["🤖 NLQ Pipeline", "🗄️ Database Explorer"])

    with tab_nlq:
        render_nlq_tab(pipeline, init_ok)

    with tab_explorer:
        render_db_explorer(pipeline)


if __name__ == "__main__":
    main()