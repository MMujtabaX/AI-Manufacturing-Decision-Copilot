# AI Manufacturing Decision Copilot — Supplier Shortlisting (Track 1)

Sofstica AI Hackathon 2026 (SGTDP, 1st cohort). Converts product requirements +
supplier profiles + quotations into a traceable, ranked, evidence-grounded
shortlist — with a transparent eligibility screen, sensitivity analysis, and
honest evaluation against a simple baseline.

## Why this design

The brief's minimum evidence for Track 1 is: (1) a transparent eligibility
screen before ranking, (2) source citations for every material supplier
claim, (3) sensitivity analysis showing how the ranking changes when
priorities change. Each maps to one module:

| Requirement | Module |
|---|---|
| Transparent eligibility screen | `src/rules.py` — plain Python, no ML, every fail names the exact rule |
| Source citations / evidence grounding | `src/extract_llm.py` — LLM only extracts facts it can quote, abstains otherwise |
| Sensitivity analysis | `src/rank.py` — named weight profiles (`cost_focused`, `speed_focused`, `quality_focused`, `balanced`) |
| Baseline + evaluation | `src/evaluate.py` — lowest-price baseline, constraint satisfaction rate, citation coverage, hallucination rate, rank agreement |

AI is used **only** where it's actually needed: normalizing messy free-text
supplier notes into structured, citable facts. The eligibility screen and
ranker are deterministic on purpose — that's what the judging rubric calls
"AI necessary rather than decorative," and it also means the core logic
still works even if the LLM API is down mid-demo.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # add your free Groq key from console.groq.com/keys (optional)
python -m pytest tests/ -q                            # should show 7 passed
streamlit run app/streamlit_app.py
```

The app runs fully **without** an API key (deterministic fallback mode for
fact extraction) — get it working end-to-end first, add the LLM key second.

## Swapping in the real case pack

Right now `data/synthetic/*.json` are hand-authored placeholders matching
the field shapes described in the brief. When the organizer's Manufacturing
Challenge Pack is released:

1. Update `data/manifest.md` with the real source URL, version, and SHA-256.
2. Write an `src/ingest.py` that maps the pack's actual format (CSV/JSON/PDF)
   into the same `ProductRequirement` / `Supplier` / `Quotation` schemas in
   `src/schema.py` — nothing downstream (rules, ranking, evaluation, UI)
   should need to change.
3. Re-run `pytest` and the Streamlit app against the real data.

## Evaluation

Run the app and check the "Evaluation" panel, or call `src/evaluate.py`
directly. Reported metrics (per the brief):
- **Mandatory-constraint satisfaction rate** — fraction of suppliers correctly screened
- **Evidence citation coverage** — fraction of extracted facts with a real source snippet
- **Hallucination rate** — measured against a seeded absent field (`export_license`); a
  correct system abstains 100% of the time
- **Ranking agreement vs. baseline** (lowest-price-only) — Spearman correlation

For the actual submission, also run `src/evaluate.py::robustness_test` with a
few fields dropped per supplier and report how the system fails safe, and add
one **ambiguous/conflicting case** and one **failure case** to the demo, as
required by "Required deliverables."

## Safety & scope (per brief)

- Decision support only — no supplier contact, RFQs, approvals, or orders.
- Every consequential recommendation shows source, date, confidence, and conflicts.
- Inferred values are never presented as verified facts.
- No confidential case-pack material is sent to external services beyond the
  declared LLM API call.

## Suggested task split (2 teammates + you)

- **You:** rules/ranking/evaluation logic, LLM extraction, ingest.py for the real pack
- **Teammate A:** Streamlit polish (charts for sensitivity analysis, better
  layout, the three required demo cases: success / ambiguous / failure)
- **Teammate B:** README/technical summary, data manifest, safety statement,
  pitch deck, demo video/recording, Sofstica portal submission (1000-char
  description, GitHub repo hygiene, CVs)

## Roadmap for the 48 hours

1. **Now:** get this skeleton running locally on synthetic data (done above).
2. **Hours 0–6 (once pack drops):** write `ingest.py`, swap synthetic data for real pack, re-run tests.
3. **Hours 6–16:** tune eligibility rules to the real requirement fields; wire up LLM extraction on real free-text fields; add 1–2 more weight profiles if the real data supports them.
4. **Hours 16–30:** build the evaluation report properly — real baseline comparison, robustness tests, the 3 required demo cases (success/ambiguous/failure).
5. **Hours 30–40:** UI polish, safety statement, technical summary/README finalize, record demo video.
6. **Hours 40–48:** buffer, rehearse pitch, submit early (portal auto-closes, no late submissions).
