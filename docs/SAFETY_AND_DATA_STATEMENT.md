# Safety & Data Statement

## Mandatory boundary (shown on every screen)
> **Decision support only.** Estimates from the supplied case pack. Supplier
> contact, approvals, quotation requests, and orders remain under explicit human
> control and are never performed by this prototype.

## Data lineage
- **100% synthetic.** `data/synthetic/{product_requirements,suppliers,quotations,scenarios,eval_cases}.json`
  are hand-authored by the team to mirror the field shapes described in the
  challenge brief (product requirements, supplier/factory profiles, quotations).
- **How generated:** manually written to exercise every rule path — suppliers that
  pass, and suppliers that fail on each distinct constraint (missing cert, MOQ too
  high, lead time too long, low quality/sustainability) — plus deliberate free-text
  tensions (a lapsed cert, a profile-vs-quotation lead-time conflict) so the LLM
  extraction and conflict detection have real work to do.
- **No real supplier data** is used, and **no confidential material** is uploaded
  anywhere. The only external call is the declared Groq LLM request for free-text
  fact extraction; the structured pipeline runs fully locally.
- **Checksums:** `data/manifest.json` records a SHA-256 for every data file
  (regenerate with `python -m src.manifest`).

## Privacy
No personal data is collected or processed. Records describe hypothetical
organizations, not individuals.

## Untrusted-input / prompt-injection stance
Supplier notes and any documents are treated as **untrusted data, not instructions.**
The extraction prompt constrains the model to a fixed JSON schema and to facts it
can quote; instructions embedded in a note are never executed, and the model
abstains when evidence is absent. The deterministic eligibility and ranking logic
cannot be influenced by note text at all.

## No inferred value presented as verified fact
Extracted facts, certifications, and lead times are shown with source snippets and
confidence, explicitly labeled as extracted/for-review — never as verified truth.
Conflicting sources are flagged, not reconciled automatically.

## Failure modes and safe states
- No eligible supplier → explicit "no recommendation" state with next steps.
- Ambiguous/unsupported note → abstain.
- Conflicting sources → surface the conflict for human review.
- LLM key missing or call fails → deterministic fallback, clearly marked in the output.

## Human-review boundary
The prototype recommends; the human decides and acts. Shortlist export is gated
behind explicit reviewer confirmation in the UI.

## Credentials handling
The Groq API key lives only in a local `.env` file, which is git-ignored and kept
out of the repository, logs, and any recording. No keys appear in source or data.
