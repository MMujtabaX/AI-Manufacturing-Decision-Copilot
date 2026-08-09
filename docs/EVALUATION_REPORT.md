# Evaluation Report

All numbers below are **computed** by `python -m src.eval` over synthetic
held-out-style cases with hand-verified expected answers. They are reproducible,
not hardcoded. Because the data is synthetic and the eligibility logic is
deterministic, treat these as a *correctness/consistency* check of the pipeline,
not as evidence of real-world supplier-selection performance.

## Baseline
Simple, credible baseline: **rank eligible suppliers by lowest unit price only**
(`src/evaluate.py::baseline_rank`). The copilot's weighted ranking is compared
against this to show it does more than pick the cheapest option.

## Metrics (synthetic eval set, 3 cases)

| Metric | Result | What it means |
|---|---|---|
| Mandatory-constraint accuracy | **100%** | Per-supplier eligibility matches the hand-verified ground truth. |
| Exact case match rate | **100%** | The full eligible set matches ground truth in every case. |
| Hallucination rate | **0%** | Measured against a seeded field (`export_license`) absent from every note — a correct system abstains 100% of the time. It does. |
| Citation coverage | **100%** | Every extracted fact either abstains or carries a source snippet. |

Reproduce:
```
python -m src.eval
python -m src.eval --cases <organizer_or_custom_cases.json>   # if a real set exists
```

## Ranking vs. baseline
In the app's evaluation panel, ranking agreement with the lowest-price baseline is
reported as a Spearman correlation. It is intentionally **less than perfect** —
the copilot balances price against lead time, quality, and sustainability, so it
diverges from a price-only order. Sensitivity analysis shows the top pick changing
across the four weight profiles, which is the point: the "best" supplier depends
on stated priorities, and the tool makes that explicit.

## The three demonstration cases
1. **Success (Scenario 1):** several suppliers pass; ranked with per-factor explanations.
2. **Ambiguous / conflicting (Scenario 2):** supplier S3's profile lead time (28d)
   conflicts with its quotation lead time (45d); the copilot flags the conflict
   instead of trusting either number.
3. **Failure / fallback (Scenario 3):** a mandatory UL certification no supplier
   holds; the copilot returns a safe "no eligible supplier" state.

## Honest limitations of this evaluation
- Synthetic data, tiny sample — this validates the *method and safety behavior*,
  not real supplier outcomes.
- Deterministic rules make constraint accuracy definitional; the value is in
  showing the rules match intended behavior and that the LLM layer abstains rather
  than fabricates.
- Hallucination is measured on a single seeded absent field; a larger seeded set
  would strengthen the claim.
