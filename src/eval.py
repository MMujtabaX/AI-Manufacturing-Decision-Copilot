"""Standalone evaluation harness.

Run OUTSIDE the Streamlit UI so judges can reproduce a benchmark log:

    python -m src.eval                       # uses data/synthetic/eval_cases.json
    python -m src.eval --cases path/to.json  # use the organizer's held-out cases

Every metric here is COMPUTED from the pipeline, not hardcoded. That matters:
the rubric penalizes unsupported claims, so a static "0% hallucination" number
is worse than a measured one. When the organizer's held-out cases are released,
point --cases at them and the same script produces the official numbers.
"""
import argparse
import json
from pathlib import Path

from .schema import ProductRequirement, Supplier
from .rules import check_eligibility
from .extract_llm import extract_fact


def run_evaluation(cases_path: str) -> dict:
    data = json.loads(Path(cases_path).read_text())
    cases = data["cases"]
    seeded_absent_fields = data.get("seeded_absent_fields", [])

    # --- Mandatory-constraint satisfaction: does our screen match ground truth? ---
    per_case = []
    total_correct_ids = 0
    total_ids = 0

    for case in cases:
        req = ProductRequirement(**case["requirements"])
        suppliers = [Supplier(**s) for s in case["suppliers"]]
        actual_eligible = {
            s.supplier_id for s in suppliers if check_eligibility(req, s).eligible
        }
        expected_eligible = set(case["expected_eligible_ids"])

        # per-supplier correctness (more informative than exact-set match)
        for s in suppliers:
            predicted = s.supplier_id in actual_eligible
            truth = s.supplier_id in expected_eligible
            total_ids += 1
            if predicted == truth:
                total_correct_ids += 1

        per_case.append({
            "case_id": case["case_id"],
            "expected_eligible": sorted(expected_eligible),
            "predicted_eligible": sorted(actual_eligible),
            "exact_match": expected_eligible == actual_eligible,
        })

    constraint_accuracy = (total_correct_ids / total_ids * 100) if total_ids else 0.0
    exact_case_match_rate = (
        sum(c["exact_match"] for c in per_case) / len(per_case) * 100 if per_case else 0.0
    )

    # --- Hallucination + citation coverage on seeded-absent fields ---
    # A correct system abstains on a field that is absent from the text.
    seeded_facts = []
    for case in cases:
        for s in case["suppliers"]:
            note = s.get("notes", "")
            for field in seeded_absent_fields:
                seeded_facts.append(extract_fact(s["supplier_id"], field, note))

    if seeded_facts:
        hallucinated = sum(1 for f in seeded_facts if not f.abstained)
        hallucination_rate = hallucinated / len(seeded_facts) * 100
        cited = sum(1 for f in seeded_facts if f.abstained or f.source_snippet)
        citation_coverage = cited / len(seeded_facts) * 100
    else:
        hallucination_rate = 0.0
        citation_coverage = 100.0

    metrics = {
        "n_cases": len(cases),
        "mandatory_constraint_accuracy_pct": round(constraint_accuracy, 2),
        "exact_case_match_rate_pct": round(exact_case_match_rate, 2),
        "hallucination_rate_pct": round(hallucination_rate, 2),
        "citation_coverage_pct": round(citation_coverage, 2),
        "per_case": per_case,
    }
    return metrics


def main():
    parser = argparse.ArgumentParser(description="Evaluate the supplier-shortlisting copilot.")
    default_cases = Path(__file__).resolve().parent.parent / "data" / "synthetic" / "eval_cases.json"
    parser.add_argument("--cases", default=str(default_cases))
    args = parser.parse_args()

    metrics = run_evaluation(args.cases)
    print("=" * 44)
    print(" MANUFACTURING COPILOT — EVALUATION RESULTS")
    print("=" * 44)
    print(json.dumps({k: v for k, v in metrics.items() if k != "per_case"}, indent=2))
    print("\nPer-case detail:")
    print(json.dumps(metrics["per_case"], indent=2))


if __name__ == "__main__":
    main()
