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
from src.evaluate import (
    baseline_rank, constraint_satisfaction_rate, citation_coverage,
    hallucination_rate, ranking_agreement,
)

st.set_page_config(page_title="Manufacturing Decision Copilot", layout="wide")

st.warning(
    "**Decision support only.** Recommendations are estimates from the supplied "
    "case pack. Supplier approval, quotation requests, and orders require explicit "
    "human confirmation and are never performed by this prototype."
)

st.title("AI Manufacturing Decision Copilot — Supplier Shortlisting")

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "synthetic"


@st.cache_data
def load_data():
    req = ProductRequirement(**json.loads((DATA_DIR / "product_requirements.json").read_text()))
    suppliers_raw = json.loads((DATA_DIR / "suppliers.json").read_text())
    quotations_raw = json.loads((DATA_DIR / "quotations.json").read_text())
    suppliers = {s["supplier_id"]: Supplier(**s) for s in suppliers_raw}
    quotations = {q["supplier_id"]: Quotation(**q) for q in quotations_raw}
    return req, suppliers, quotations


req, suppliers, quotations = load_data()

st.caption(f"Product requirement: **{req.product_name}** — mandatory certs: "
           f"{', '.join(req.mandatory_certifications)}; MOQ <= {req.min_order_quantity_max}; "
           f"lead time <= {req.max_lead_time_days}d")

st.subheader("1. Eligibility screen (transparent, rule-based)")
elig_results = [check_eligibility(req, s) for s in suppliers.values()]
elig_df = pd.DataFrame([{
    "Supplier": suppliers[r.supplier_id].name,
    "Eligible": "PASS" if r.eligible else "FAIL",
    "Reasons": "; ".join(r.reasons),
} for r in elig_results])
st.dataframe(elig_df, use_container_width=True, hide_index=True)

eligible_ids = [r.supplier_id for r in elig_results if r.eligible]
st.caption(f"{len(eligible_ids)} of {len(elig_results)} suppliers passed mandatory screening.")

st.subheader("2. Ranking")
profile = st.selectbox("Priority profile", list(WEIGHT_PROFILES.keys()), index=0)
ranked = rank_suppliers(eligible_ids, suppliers, quotations, profile)
rank_df = pd.DataFrame([{
    "Rank": r.rank, "Supplier": r.name, "Score": r.score,
    "Explanation": r.explanation,
} for r in ranked])
st.dataframe(rank_df, use_container_width=True, hide_index=True)

st.subheader("3. Sensitivity analysis — does the top pick change with priorities?")
sens = sensitivity_analysis(eligible_ids, suppliers, quotations)
top_by_profile = {p: (rs[0].name if rs else "—") for p, rs in sens.items()}
st.table(pd.DataFrame(top_by_profile.items(), columns=["Profile", "Top supplier"]))

st.subheader("4. Evidence extraction from free-text supplier notes (LLM-assisted, abstains when unsupported)")
st.caption("Set GROQ_API_KEY in your environment to use the LLM; otherwise this runs in "
           "deterministic fallback mode so the demo never breaks.")
facts = [extract_fact(sid, "certification", suppliers[sid].notes) for sid in suppliers]
facts_df = pd.DataFrame([{
    "Supplier": suppliers[f.supplier_id].name, "Field": f.field,
    "Value": f.value, "Source snippet": f.source_snippet,
    "Confidence": f.confidence, "Abstained": f.abstained,
} for f in facts])
st.dataframe(facts_df, use_container_width=True, hide_index=True)

st.subheader("5. Evaluation vs. baseline (lowest-price-only ranking)")
b_rank = baseline_rank(eligible_ids, quotations)
system_rank_ids = [r.supplier_id for r in ranked]
col1, col2, col3, col4 = st.columns(4)
col1.metric("Constraint satisfaction", f"{constraint_satisfaction_rate(elig_results):.0%}")
col2.metric("Citation coverage", f"{citation_coverage(facts):.0%}")
col3.metric("Hallucination rate*", f"{hallucination_rate(facts, ['export_license']):.0%}")
col4.metric("Rank agreement vs baseline", f"{ranking_agreement(system_rank_ids, b_rank):.2f}")
st.caption("*Hallucination rate is measured against a seeded field ('export_license') "
           "known to be absent from every supplier's notes -- a correct system abstains on all of them.")
