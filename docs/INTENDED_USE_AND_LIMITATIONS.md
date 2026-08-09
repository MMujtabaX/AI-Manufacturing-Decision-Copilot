# Intended Use, Assumptions & Limitations

## Intended user
A procurement or sourcing analyst at a product company who currently spends hours
manually cross-referencing supplier profiles, quotations, and requirement sheets
before they can compare options or justify a shortlist.

## The decision it supports
"Given this product requirement, which suppliers are eligible, how should they be
ranked, and what evidence backs each claim?" — delivered as a transparent
eligibility screen, a ranked shortlist with explanations, flagged conflicts, and
cited facts.

## Success criteria
- Correctly screens suppliers against mandatory constraints (measured: constraint accuracy).
- Never presents an unsupported claim as fact (measured: hallucination rate via a seeded absent field).
- Shows how the ranking shifts when priorities change (sensitivity analysis).
- Fails safe when no supplier qualifies or when sources conflict.
- Cuts the analyst's manual cross-referencing time versus doing it by hand.

## Scope and limits
- **Decision support only.** It does not contact suppliers, request quotations,
  approve vendors, or place orders.
- **Synthetic data.** All supplier/quotation records are hand-authored synthetic
  data (see `docs/SAFETY_AND_DATA_STATEMENT.md`). Results demonstrate the method;
  they are not statements about real suppliers or real-world performance.
- **Not a compliance, legal, customs, or engineering authority.** Certification
  and export-control notes are flagged for human verification, never certified.

## Assumptions
- Provided scores (quality, sustainability) and requirement thresholds are trusted inputs.
- One product requirement per run; multi-line BOM sourcing is out of scope for this prototype.
- Location preference is soft; only certifications, MOQ, lead time, quality, and
  sustainability thresholds are hard constraints.

## Known limitations and failure modes
- If every supplier fails a mandatory constraint, the copilot returns a **safe
  "no eligible supplier" state** rather than forcing a pick (demonstrated in Scenario 3).
- If a note is ambiguous or unsupported, extraction **abstains** rather than guess.
- Structured fields and free-text notes can disagree (by design in the synthetic
  set); the copilot surfaces this for the human rather than auto-resolving it.
- Ranking is a transparent weighted score, not a learned model; it reflects the
  chosen weight profile, which is why sensitivity analysis is shown alongside it.

## Human-approval points
Shortlist export is gated behind an explicit reviewer confirmation. Any real
sourcing action (contact, RFQ, approval, order) remains entirely with the human.
