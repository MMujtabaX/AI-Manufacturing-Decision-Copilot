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

st.set_page_config(page_title="AI Manufacturing Decision Copilot", layout="wide")

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "synthetic"


@st.cache_data
def load_base():
    suppliers_raw = json.loads((DATA_DIR / "suppliers.json").read_text())
    quotations_raw = json.loads((DATA_DIR / "quotations.json").read_text())
    scenarios = json.loads((DATA_DIR / "scenarios.json").read_text())["scenarios"]
    suppliers = {s["supplier_id"]: Supplier(**s) for s in suppliers_raw}
    quotations = {q["supplier_id"]: Quotation(**q) for q in quotations_raw}
    return suppliers, quotations, scenarios


suppliers, quotations, scenarios = load_base()

# --- Mandatory safety banner (required by brief on every screen) ---
st.warning(
    "**Decision support only.** Estimates from the supplied case pack. Supplier "
    "contact, approvals, quotation requests, and orders remain under explicit human "
    "control and are never performed by this prototype."
)
st.title("AI Manufacturing Decision Copilot — Supplier Shortlisting")

# --- Scenario selector (the 3 required demo cases) ---
scenario_key = st.sidebar.selectbox(
    "Demo scenario",
    list(scenarios.keys()),
    format_func=lambda k: scenarios[k]["label"],
)
scenario = scenarios[scenario_key]
req = ProductRequirement(**scenario["requirements"])
st.sidebar.caption(scenario["description"])
st.info(f"**{scenario['label']}** — {scenario['description']}")

st.caption(
    f"Requirement: **{req.product_name}** — mandatory certs: "
    f"{', '.join(req.mandatory_certifications)}; MOQ ≤ {req.min_order_quantity_max}; "
    f"lead time ≤ {req.max_lead_time_days}d; min quality "
    f"{req.min_quality_history_score}; min sustainability {req.min_sustainability_score}"
)

tab_decision, tab_evidence, tab_bench = st.tabs(
    ["Decision dashboard", "Evidence & conflicts", "Benchmarks (eval.py)"]
)

# ------------------------------------------------------------------ DECISION
with tab_decision:
    st.subheader("1. Eligibility screen (transparent, rule-based)")
    elig_results = [check_eligibility(req, s) for s in suppliers.values()]
    elig_df = pd.DataFrame([{
        "Supplier": suppliers[r.supplier_id].name,
        "Result": "PASS" if r.eligible else "FAIL",
        "Reasons": "; ".join(r.reasons),
    } for r in elig_results])
    st.dataframe(elig_df, use_container_width=True, hide_index=True)

    eligible_ids = [r.supplier_id for r in elig_results if r.eligible]

    if not eligible_ids:
        # Safe failure state (Scenario 3)
        st.error(
            "**No eligible supplier.** Every candidate failed at least one mandatory "
            "constraint, so the copilot abstains rather than forcing a recommendation. "
            "Next step for a human reviewer: relax a non-critical constraint, request "
            "missing certifications, or expand the supplier pool."
        )
    else:
        st.caption(f"{len(eligible_ids)} of {len(elig_results)} suppliers passed screening.")

        st.subheader("2. Ranking")
        profile = st.selectbox("Priority profile", list(WEIGHT_PROFILES.keys()), index=0)
        ranked = rank_suppliers(eligible_ids, suppliers, quotations, profile)
        rank_df = pd.DataFrame([{
            "Rank": r.rank, "Supplier": r.name, "Score": r.score, "Explanation": r.explanation,
        } for r in ranked])
        st.dataframe(rank_df, use_container_width=True, hide_index=True)

        st.subheader("3. Sensitivity analysis — does the top pick change with priorities?")
        sens = sensitivity_analysis(eligible_ids, suppliers, quotations)
        top_by_profile = {p: (rs[0].name if rs else "—") for p, rs in sens.items()}
        st.table(pd.DataFrame(top_by_profile.items(), columns=["Priority profile", "Top supplier"]))

        # --- Human approval gate (required human-control checkpoint) ---
        st.subheader("4. Human approval checkpoint")
        st.caption("The copilot recommends; a human decides. Downstream actions stay disabled "
                   "until a reviewer confirms they have checked the evidence and conflicts.")
        approved = st.checkbox("I have reviewed the ranking, evidence, and any flagged conflicts.")
        st.button(
            "Export shortlist for human sign-off",
            disabled=not approved,
            help="Writes a local shortlist file for a human buyer. Never contacts a supplier "
                 "or sends an RFQ.",
        )
        if not approved:
            st.caption("Export disabled until the review box is checked.")

# ------------------------------------------------------------------ EVIDENCE
with tab_evidence:
    st.subheader("Cross-source conflicts (profile vs. quotation)")
    conflicts = detect_conflicts(suppliers, quotations)
    if conflicts:
        conf_df = pd.DataFrame([{
            "Supplier": suppliers[c.supplier_id].name,
            "Field": c.field,
            "Profile value": c.profile_value,
            "Quote value": c.quote_value,
            "Detail": c.detail,
        } for c in conflicts])
        st.dataframe(conf_df, use_container_width=True, hide_index=True)
        st.caption("The copilot does not silently pick a value when sources disagree — it flags "
                   "the conflict for the human reviewer.")
    else:
        st.success("No cross-source conflicts detected in this data.")

    st.subheader("Evidence extraction from free-text notes (LLM-assisted, abstains when unsupported)")
    st.caption("Set GROQ_API_KEY to use the LLM; otherwise runs in deterministic fallback mode so "
               "the demo never breaks.")
    facts = [extract_fact(sid, "certification", suppliers[sid].notes) for sid in suppliers]
    facts_df = pd.DataFrame([{
        "Supplier": suppliers[f.supplier_id].name, "Field": f.field, "Value": f.value,
        "Source snippet": f.source_snippet, "Confidence": f.confidence, "Abstained": f.abstained,
    } for f in facts])
    st.dataframe(facts_df, use_container_width=True, hide_index=True)

# ------------------------------------------------------------------ BENCHMARKS
with tab_bench:
    st.subheader("Automated evaluation (computed, not hardcoded)")
    st.caption("These numbers come from `python -m src.eval` running over held-out-style eval "
               "cases with hand-verified answers. Point it at the organizer's held-out cases "
               "when they're released.")
    metrics = run_evaluation(str(DATA_DIR / "eval_cases.json"))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Constraint accuracy", f"{metrics['mandatory_constraint_accuracy_pct']:.0f}%")
    c2.metric("Exact case match", f"{metrics['exact_case_match_rate_pct']:.0f}%")
    c3.metric("Hallucination rate", f"{metrics['hallucination_rate_pct']:.0f}%")
    c4.metric("Citation coverage", f"{metrics['citation_coverage_pct']:.0f}%")
    with st.expander("Per-case detail"):
        st.json(metrics["per_case"])
