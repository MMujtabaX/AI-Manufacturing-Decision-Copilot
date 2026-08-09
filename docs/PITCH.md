# Pitch — Manufacturing Decision Copilot

## The 90-second story
1. **Problem.** A procurement analyst sourcing a part juggles supplier profiles,
   quotations, and a requirement sheet across spreadsheets and PDFs. Cross-checking
   who's eligible and why takes hours, and the reasoning is hard to audit.
2. **What we built.** A supplier-shortlisting copilot that turns those inputs into
   a ranked, explained shortlist — with cited evidence, flagged conflicts, and a
   human-approval gate before anything leaves the tool.
3. **The key idea — dual engine.** Hard numeric rules (certs, MOQ, lead time,
   thresholds) run in deterministic Python: 0% hallucination, fully auditable. The
   LLM is used *only* where rules fail — reading messy free-text notes into cited
   facts, and abstaining when the text doesn't support an answer. AI where it's
   necessary, not decorative.
4. **Live demo (the three cases, from the sidebar):**
   - *Success:* eligible suppliers ranked with per-factor explanations; flip the
     priority profile to show the top pick change — that's built-in sensitivity analysis.
   - *Ambiguous:* S3's profile says 28-day lead time, its quote says 45 — we flag
     the conflict instead of trusting either.
   - *Failure:* require a cert nobody holds → safe "no eligible supplier" state, no forced pick.
5. **Evidence.** `python -m src.eval`: 100% constraint accuracy, 0% hallucination
   (measured against a seeded absent field), 100% citation coverage. All computed, reproducible.
6. **Safety & honesty.** Decision-support only — no supplier contact, RFQ, or
   orders. Data is 100% synthetic and labeled as such; nothing claims real-world
   performance. Key stays in a git-ignored `.env`.
7. **What we'd add with more time.** Real case-pack ingestion, a larger seeded
   hallucination set, and landed-cost comparison (Track 2) on the same engine.

## Suggested slides (6)
1. **Title + one-line problem** — "Hours of manual supplier cross-referencing, made auditable."
2. **User & decision** — the analyst, and the shortlist decision they own.
3. **Architecture** — the dual-engine data-flow diagram from the method card.
4. **Live demo** — the three scenarios (this is where you spend the most time).
5. **Evidence & safety** — the eval table + the human-approval gate + synthetic-data honesty.
6. **Limitations & next steps** — what's synthetic, what you'd validate next.

## Rubric hooks (say these out loud)
- **Problem & Impact (20%):** named user, real time-cost, measurable proxy value.
- **AI & Data Quality (25%):** dual engine, deterministic constraints, abstention, reproducible eval.
- **Working Product (20%):** end-to-end, three failure/edge cases handled live.
- **Safety & Reliability (15%):** human gate, no verified-fact claims, synthetic-data disclosure, key hygiene.
- **Innovation (10%):** the dual-engine split — differentiation without unnecessary complexity.
- **Pitch & Clarity (10%):** traceable source-to-output reasoning shown on screen.
