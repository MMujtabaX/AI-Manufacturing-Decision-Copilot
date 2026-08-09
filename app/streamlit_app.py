import json
import sys
from pathlib import Path

import streamlit as st
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.schema import ProductRequirement, Supplier, Quotation
from src.rules import check_eligibility
from src.rank import rank_suppliers, sensitivity_analysis, WEIGHT_PROFILES
from src.extract_llm import extract_fact
from src.conflicts import detect_conflicts
from src.evaluate import (
    baseline_rank, constraint_satisfaction_rate, citation_coverage,
    hallucination_rate, ranking_agreement,
)
from src.eval import run_evaluation

st.set_page_config(page_title="SourceWise — Supplier Shortlisting",
                   page_icon="▪", layout="wide")

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "synthetic"

# ----------------------------------------------------------------- styling
STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root{
  --navy:#1B2A4A; --slate:#334155; --grey:#5A6472; --line:#DCE0E6;
  --panel:#F1F3F5; --panel2:#F7F8FA; --ok:#1E6B4F; --warn:#8A5A00; --bad:#8C2F27;
}
html, body, .stApp, p, div, span, label, td, th, li,
h1, h2, h3, h4, h5, h6, button, input, textarea, select,
[data-testid="stMarkdownContainer"]{
  font-family:'IBM Plex Sans', -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
}
code, pre, kbd, [data-testid="stCodeBlock"] *{ font-family:'IBM Plex Mono', monospace; }

.stApp{ background:#FFFFFF; }
[data-testid="stHeader"]{ background:transparent; }
[data-testid="stToolbar"]{ display:none; }
footer{ visibility:hidden; }
.block-container{ padding-top:2.2rem; max-width:1200px; }

h1,h2,h3{ color:var(--navy); letter-spacing:-0.01em; }
h2{ font-weight:600; font-size:1.3rem; margin-top:0.6rem; }
h3{ font-weight:600; font-size:1.05rem; }

.sw-header{ padding:0 0 0.7rem 0; border-bottom:1px solid var(--line); margin-bottom:1.1rem; }
.sw-title{ font-size:1.85rem; font-weight:700; color:var(--navy); vertical-align:middle; }
.sw-chip{ display:inline-block; background:var(--panel); color:var(--slate);
  border:1px solid var(--line); border-radius:999px; padding:2px 11px;
  font-size:0.68rem; font-weight:600; letter-spacing:0.08em; vertical-align:middle;
  margin-left:0.5rem; }
.sw-sub{ color:var(--grey); font-size:0.95rem; margin-top:0.15rem; }

.sw-notice{ background:var(--panel2); border:1px solid var(--line);
  border-left:3px solid var(--navy); border-radius:6px; padding:0.7rem 0.95rem;
  color:var(--slate); font-size:0.9rem; margin:0.2rem 0 1.1rem; }
.sw-notice b{ color:var(--navy); }

.sw-panel{ background:var(--panel); border:1px solid var(--line); border-radius:6px;
  padding:0.6rem 0.9rem; color:var(--slate); font-size:0.9rem; margin:0.2rem 0 0.9rem; }
.sw-panel b{ color:var(--navy); }

.sw-caption{ color:var(--grey); font-size:0.82rem; }

[data-testid="stMetricValue"]{ color:var(--navy); font-weight:700; }
[data-testid="stMetricLabel"]{ color:var(--grey); text-transform:uppercase;
  letter-spacing:0.05em; font-size:0.72rem; }

.stButton>button{ background:var(--navy); color:#fff; border:1px solid var(--navy);
  border-radius:6px; font-weight:600; padding:0.4rem 1rem; }
.stButton>button:hover{ background:#243656; border-color:#243656; color:#fff; }
.stButton>button:disabled{ background:#E5E8EC; color:#9AA3AF; border-color:var(--line); }

.stTabs [data-baseweb="tab-list"]{ gap:0.4rem; border-bottom:1px solid var(--line); }
.stTabs [data-baseweb="tab"]{ font-weight:600; color:var(--grey); }
.stTabs [aria-selected="true"]{ color:var(--navy); }

[data-testid="stDataFrame"]{ border:1px solid var(--line); border-radius:8px; }
[data-testid="stSidebar"]{ background:var(--panel2); border-right:1px solid var(--line); }
[data-testid="stSidebar"] .sw-caption{ font-size:0.8rem; }

.sw-foot{ margin-top:2rem; padding-top:0.8rem; border-top:1px solid var(--line);
  color:var(--grey); font-size:0.78rem; }
</style>
"""
st.markdown(STYLE, unsafe_allow_html=True)


@st.cache_data
def load_base():
    suppliers_raw = json.loads((DATA_DIR / "suppliers.json").read_text())
    quotations_raw = json.loads((DATA_DIR / "quotations.json").read_text())
    scenarios = json.loads((DATA_DIR / "scenarios.json").read_text())["scenarios"]
    suppliers = {s["supplier_id"]: Supplier(**s) for s in suppliers_raw}
    quotations = {q["supplier_id"]: Quotation(**q) for q in quotations_raw}
    return suppliers, quotations, scenarios


suppliers, quotations, scenarios = load_base()

# ----------------------------------------------------------------- header
st.markdown(
    '<div class="sw-header">'
    '<span class="sw-title">SourceWise</span>'
    '<span class="sw-chip">SYNTHETIC DATA · DEMO</span>'
    '<div class="sw-sub">AI Manufacturing Decision Copilot · Supplier Shortlisting</div>'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="sw-notice"><b>Decision support only.</b> Estimates from the supplied '
    'case pack. Supplier contact, approvals, quotation requests, and orders remain under '
    'explicit human control and are never performed by this prototype.</div>',
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------- scenario
scenario_key = st.sidebar.selectbox(
    "Demo scenario", list(scenarios.keys()),
    format_func=lambda k: scenarios[k]["label"],
)
scenario = scenarios[scenario_key]
req = ProductRequirement(**scenario["requirements"])
st.sidebar.markdown(f'<div class="sw-caption">{scenario["description"]}</div>',
                    unsafe_allow_html=True)

st.markdown(
    f'<div class="sw-panel"><b>{scenario["label"]}</b><br>{scenario["description"]}</div>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<div class="sw-caption">Requirement: <b>{req.product_name}</b> · mandatory certs: '
    f'{", ".join(req.mandatory_certifications)} · MOQ ≤ {req.min_order_quantity_max} · '
    f'lead time ≤ {req.max_lead_time_days}d · min quality {req.min_quality_history_score} · '
    f'min sustainability {req.min_sustainability_score}</div>',
    unsafe_allow_html=True,
)

tab_decision, tab_evidence, tab_bench = st.tabs(
    ["Decision dashboard", "Evidence & conflicts", "Benchmarks"]
)

# ------------------------------------------------------------------ DECISION
with tab_decision:
    st.subheader("1 · Eligibility screen")
    st.markdown('<div class="sw-caption">Transparent, rule-based. Every result names the '
                'exact constraint.</div>', unsafe_allow_html=True)
    elig_results = [check_eligibility(req, s) for s in suppliers.values()]
    elig_df = pd.DataFrame([{
        "Supplier": suppliers[r.supplier_id].name,
        "Result": "PASS" if r.eligible else "FAIL",
        "Reasons": "; ".join(r.reasons),
    } for r in elig_results])
    st.dataframe(elig_df, use_container_width=True, hide_index=True)

    eligible_ids = [r.supplier_id for r in elig_results if r.eligible]

    if not eligible_ids:
        st.markdown(
            '<div class="sw-notice" style="border-left-color:#8C2F27;">'
            '<b>No eligible supplier.</b> Every candidate failed at least one mandatory '
            'constraint, so the copilot abstains rather than forcing a recommendation. '
            'Next step for a reviewer: relax a non-critical constraint, request missing '
            'certifications, or expand the supplier pool.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f'<div class="sw-caption">{len(eligible_ids)} of {len(elig_results)} '
                    f'suppliers passed screening.</div>', unsafe_allow_html=True)

        st.subheader("2 · Ranking")
        profile = st.selectbox("Priority profile", list(WEIGHT_PROFILES.keys()), index=0)
        ranked = rank_suppliers(eligible_ids, suppliers, quotations, profile)
        rank_df = pd.DataFrame([{
            "Rank": r.rank, "Supplier": r.name, "Score": r.score, "Explanation": r.explanation,
        } for r in ranked])
        st.dataframe(rank_df, use_container_width=True, hide_index=True)

        st.subheader("3 · Sensitivity analysis")
        st.markdown('<div class="sw-caption">Does the top pick change when priorities '
                    'change?</div>', unsafe_allow_html=True)
        sens = sensitivity_analysis(eligible_ids, suppliers, quotations)
        top_by_profile = {p: (rs[0].name if rs else "—") for p, rs in sens.items()}
        st.table(pd.DataFrame(top_by_profile.items(),
                              columns=["Priority profile", "Top supplier"]))

        st.subheader("4 · Human approval checkpoint")
        st.markdown('<div class="sw-caption">The copilot recommends; a human decides. '
                    'Export stays disabled until a reviewer confirms.</div>',
                    unsafe_allow_html=True)
        approved = st.checkbox("I have reviewed the ranking, evidence, and any flagged conflicts.")
        st.button("Export shortlist for human sign-off", disabled=not approved,
                  help="Writes a local shortlist for a human buyer. Never contacts a "
                       "supplier or sends an RFQ.")
        if not approved:
            st.markdown('<div class="sw-caption">Export disabled until the review box is '
                        'checked.</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------ EVIDENCE
with tab_evidence:
    st.subheader("Cross-source conflicts")
    st.markdown('<div class="sw-caption">Profile vs. quotation. The copilot flags '
                'disagreements instead of silently choosing a value.</div>',
                unsafe_allow_html=True)
    conflicts = detect_conflicts(suppliers, quotations)
    if conflicts:
        conf_df = pd.DataFrame([{
            "Supplier": suppliers[c.supplier_id].name, "Field": c.field,
            "Profile value": c.profile_value, "Quote value": c.quote_value, "Detail": c.detail,
        } for c in conflicts])
        st.dataframe(conf_df, use_container_width=True, hide_index=True)
    else:
        st.markdown('<div class="sw-panel">No cross-source conflicts detected in this '
                    'data.</div>', unsafe_allow_html=True)

    st.subheader("Evidence extraction from free-text notes")
    st.markdown('<div class="sw-caption">LLM-assisted, abstains when unsupported. Set '
                'GROQ_API_KEY to use the LLM; otherwise a deterministic fallback runs so the '
                'demo never breaks.</div>', unsafe_allow_html=True)
    facts = [extract_fact(sid, "certification", suppliers[sid].notes) for sid in suppliers]
    facts_df = pd.DataFrame([{
        "Supplier": suppliers[f.supplier_id].name, "Field": f.field, "Value": f.value,
        "Source snippet": f.source_snippet, "Confidence": f.confidence, "Abstained": f.abstained,
    } for f in facts])
    st.dataframe(facts_df, use_container_width=True, hide_index=True)

# ------------------------------------------------------------------ BENCHMARKS
with tab_bench:
    st.subheader("Automated evaluation")
    st.markdown('<div class="sw-caption">Computed by <code>python -m src.eval</code> over '
                'held-out-style cases with hand-verified answers. Not hardcoded.</div>',
                unsafe_allow_html=True)
    metrics = run_evaluation(str(DATA_DIR / "eval_cases.json"))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Constraint accuracy", f"{metrics['mandatory_constraint_accuracy_pct']:.0f}%")
    c2.metric("Exact case match", f"{metrics['exact_case_match_rate_pct']:.0f}%")
    c3.metric("Hallucination rate", f"{metrics['hallucination_rate_pct']:.0f}%")
    c4.metric("Citation coverage", f"{metrics['citation_coverage_pct']:.0f}%")
    with st.expander("Per-case detail"):
        st.json(metrics["per_case"])

# ------------------------------------------------------------------ footer
st.markdown(
    '<div class="sw-foot">SourceWise · research/demo prototype · all supplier data is '
    'synthetic and does not represent real suppliers or real-world performance.</div>',
    unsafe_allow_html=True,
)