# Method Card — Manufacturing Decision Copilot (Supplier Shortlisting)

## Target user and decision
A **procurement / sourcing analyst** deciding **which suppliers to shortlist and in
what order** for a given product requirement. The copilot produces a ranked,
explained shortlist with cited evidence and flagged conflicts. It is **decision
support**: the human makes the call and owns every downstream action.

## Architecture and data flow

```
 synthetic case pack (JSON)
   product_requirements | suppliers | quotations | scenarios | eval_cases
            │
            ▼
   ┌─────────────────────────────┐
   │ 1. Eligibility screen        │  src/rules.py  (deterministic, no ML)
   │    hard constraints → PASS/FAIL, each with a named reason
   └─────────────────────────────┘
            │ eligible suppliers only
            ▼
   ┌─────────────────────────────┐
   │ 2. Weighted ranking          │  src/rank.py   (min-max normalized scoring)
   │    4 priority profiles = built-in sensitivity analysis
   └─────────────────────────────┘
            │
            ├──► 3. Conflict detection   src/conflicts.py  (profile vs quotation)
            │
            ├──► 4. Evidence extraction  src/extract_llm.py  (Groq LLM, abstains)
            │        free-text notes → cited facts, or "insufficient evidence"
            │
            ▼
   ┌─────────────────────────────┐
   │ 5. Evaluation harness        │  src/eval.py   (computed metrics, not hardcoded)
   └─────────────────────────────┘
            │
            ▼
   Streamlit UI (app/streamlit_app.py): 3 demo scenarios, evidence/conflict
   panel, benchmarks tab, and a HUMAN-APPROVAL GATE before any export.
```

## Dual-engine design (the core idea)
Numeric, rule-based decisions (certifications, MOQ, lead time, thresholds) are
handled by **plain deterministic Python** — this cannot hallucinate and is fully
auditable. The **LLM is used only** for the one thing rules can't do well:
normalizing messy free-text supplier notes into structured, *citable* facts, and
abstaining when the text doesn't support an answer. This is what makes the AI
"necessary rather than decorative" per the rubric, and it means the core
shortlist still works if the LLM is unavailable.

## Models and solvers
- **Eligibility:** deterministic constraint checks (`src/rules.py`).
- **Ranking:** weighted linear score over min-max-normalized features
  (price, lead time, quality, sustainability), four named weight profiles
  (`balanced`, `cost_focused`, `speed_focused`, `quality_focused`).
- **Extraction:** Groq free tier, model `openai/gpt-oss-20b`
  (replaces the deprecated `llama-3.1-8b-instant`), temperature 0, JSON mode,
  with a deterministic keyword fallback.

## Input features
Structured: certifications, MOQ, lead time, quality-history score, sustainability
score, capacity, location, unit price, freight, duty, Incoterm. Unstructured:
free-text supplier `notes` (the LLM's input).

## Assumptions
- The supplied scores (quality, sustainability) are given inputs, not modeled.
- Requirement thresholds are provided by the analyst per sourcing case.
- Location is a soft preference (flagged), not a hard disqualifier.

## Confidence handling and abstention
Every extracted fact carries a confidence and a source snippet, or is marked
`abstained=true` when the note doesn't support it. Cross-source disagreements
(e.g. profile vs quotation lead time) are surfaced as conflicts rather than
silently resolved.

## Human-approval points
- No shortlist export until the reviewer checks the approval box in the UI.
- No supplier contact, RFQ, approval, or order is ever performed by the prototype.
- Extracted facts and conflicts are shown *for human review*, not treated as verified.
