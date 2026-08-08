"""Weighted scoring + sensitivity analysis for eligible suppliers.

The brief explicitly wants to see "how the ranking changes when priorities
change" -- so ranking is driven by named weight profiles rather than one
hard-coded formula. Adding/editing a profile IS the sensitivity analysis.
"""
from typing import Dict, List
from .schema import Supplier, Quotation, RankedSupplier

WEIGHT_PROFILES: Dict[str, Dict[str, float]] = {
    "balanced": {"price": 0.30, "lead_time": 0.25, "quality": 0.25, "sustainability": 0.20},
    "cost_focused": {"price": 0.55, "lead_time": 0.15, "quality": 0.20, "sustainability": 0.10},
    "speed_focused": {"price": 0.15, "lead_time": 0.55, "quality": 0.20, "sustainability": 0.10},
    "quality_focused": {"price": 0.15, "lead_time": 0.15, "quality": 0.55, "sustainability": 0.15},
}


def _normalize(values: Dict[str, float], invert: bool = False) -> Dict[str, float]:
    if not values:
        return {}
    lo, hi = min(values.values()), max(values.values())
    if hi == lo:
        return {k: 1.0 for k in values}
    if invert:  # lower raw value = better (price, lead time)
        return {k: (hi - v) / (hi - lo) for k, v in values.items()}
    return {k: (v - lo) / (hi - lo) for k, v in values.items()}


def rank_suppliers(
    eligible_ids: List[str],
    suppliers: Dict[str, Supplier],
    quotations: Dict[str, Quotation],
    profile: str = "balanced",
) -> List[RankedSupplier]:
    weights = WEIGHT_PROFILES[profile]

    prices = {sid: quotations[sid].unit_price for sid in eligible_ids if sid in quotations}
    lead_times = {sid: suppliers[sid].lead_time_days for sid in eligible_ids
                  if suppliers[sid].lead_time_days is not None}
    quality = {sid: suppliers[sid].quality_history_score for sid in eligible_ids
               if suppliers[sid].quality_history_score is not None}
    sustainability = {sid: suppliers[sid].sustainability_score for sid in eligible_ids
                       if suppliers[sid].sustainability_score is not None}

    norm_price = _normalize(prices, invert=True)
    norm_lead = _normalize(lead_times, invert=True)
    norm_quality = _normalize(quality)
    norm_sustain = _normalize(sustainability)

    results = []
    for sid in eligible_ids:
        breakdown = {
            "price": round(norm_price.get(sid, 0.5) * weights["price"], 4),
            "lead_time": round(norm_lead.get(sid, 0.5) * weights["lead_time"], 4),
            "quality": round(norm_quality.get(sid, 0.5) * weights["quality"], 4),
            "sustainability": round(norm_sustain.get(sid, 0.5) * weights["sustainability"], 4),
        }
        score = round(sum(breakdown.values()), 4)
        explanation = (
            f"Scored {score:.3f} under '{profile}' weighting -- "
            f"price contributed {breakdown['price']:.3f}, lead time {breakdown['lead_time']:.3f}, "
            f"quality {breakdown['quality']:.3f}, sustainability {breakdown['sustainability']:.3f}."
        )
        results.append(RankedSupplier(
            supplier_id=sid, name=suppliers[sid].name, score=score,
            rank=0, score_breakdown=breakdown, explanation=explanation,
        ))

    results.sort(key=lambda r: r.score, reverse=True)
    for i, r in enumerate(results, start=1):
        r.rank = i
    return results


def sensitivity_analysis(eligible_ids, suppliers, quotations) -> Dict[str, List[RankedSupplier]]:
    return {profile: rank_suppliers(eligible_ids, suppliers, quotations, profile)
            for profile in WEIGHT_PROFILES}
