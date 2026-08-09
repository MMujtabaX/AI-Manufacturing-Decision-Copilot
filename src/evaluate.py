"""Evaluation report generator.

Computes the metrics the brief explicitly requires: mandatory-constraint
satisfaction rate, evidence citation coverage, unsupported-claim/
hallucination rate, ranking agreement vs a simple baseline, and robustness
under missing fields.
"""
from typing import Dict, List
from scipy.stats import spearmanr
from .schema import Supplier, Quotation, EligibilityResult
from .rules import check_eligibility


def baseline_rank(eligible_ids: List[str], quotations: Dict[str, Quotation]) -> List[str]:
    """Required simple baseline: rank purely by lowest unit price."""
    return sorted(eligible_ids, key=lambda sid: quotations[sid].unit_price)


def constraint_satisfaction_rate(eligibility_results: List[EligibilityResult]) -> float:
    if not eligibility_results:
        return 0.0
    return sum(r.eligible for r in eligibility_results) / len(eligibility_results)


def citation_coverage(facts) -> float:
    if not facts:
        return 1.0  # nothing needed extraction
    covered = sum(1 for f in facts if not f.abstained and f.source_snippet)
    return covered / len(facts)


def hallucination_rate(facts, seeded_absent_fields: List[str]) -> float:
    """Seed (field) values known to be absent from every supplier's text.
    A correct system abstains on all of them; any non-abstained 'fact' on a
    seeded-absent field counts as a hallucination."""
    seeded = [f for f in facts if f.field in seeded_absent_fields]
    if not seeded:
        return 0.0
    hallucinated = sum(1 for f in seeded if not f.abstained)
    return hallucinated / len(seeded)


def ranking_agreement(system_rank: List[str], baseline_rank_ids: List[str]) -> float:
    if len(system_rank) < 2:
        return 1.0
    common = [s for s in system_rank if s in baseline_rank_ids]
    if len(common) < 2:
        return 1.0
    b_order = [baseline_rank_ids.index(s) for s in common]
    s_order = [system_rank.index(s) for s in common]
    corr, _ = spearmanr(s_order, b_order)
    return float(corr) if corr == corr else 0.0  # guard against NaN


def robustness_test(req, suppliers: Dict[str, Supplier], drop_field: str) -> Dict[str, EligibilityResult]:
    """Re-run eligibility with one field nulled out per supplier, to confirm
    the system fails safe (flags as insufficient) rather than guessing."""
    results = {}
    for sid, s in suppliers.items():
        s_copy = s.model_copy(deep=True)
        setattr(s_copy, drop_field, None)
        results[sid] = check_eligibility(req, s_copy)
    return results
