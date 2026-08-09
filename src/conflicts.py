"""Cross-source conflict detection.

Surfaces the brief's canonical 'ambiguous / conflicting' case: the supplier
profile and the quotation disagree on the same fact (e.g. lead time). The
copilot never silently picks one -- it flags the conflict for the human
reviewer, which is exactly the behavior the safety rules require.
"""
from typing import Dict, List, Optional
from .schema import Supplier, Quotation

LEAD_TIME_TOLERANCE_DAYS = 3
MOQ_TOLERANCE = 0


class Conflict:
    def __init__(self, supplier_id: str, field: str, profile_value, quote_value, detail: str):
        self.supplier_id = supplier_id
        self.field = field
        self.profile_value = profile_value
        self.quote_value = quote_value
        self.detail = detail

    def as_dict(self):
        return {
            "supplier_id": self.supplier_id,
            "field": self.field,
            "profile_value": self.profile_value,
            "quote_value": self.quote_value,
            "detail": self.detail,
        }


def detect_conflicts(suppliers: Dict[str, Supplier],
                     quotations: Dict[str, Quotation]) -> List[Conflict]:
    conflicts: List[Conflict] = []
    for sid, supplier in suppliers.items():
        quote: Optional[Quotation] = quotations.get(sid)
        if quote is None:
            continue

        if supplier.lead_time_days is not None:
            diff = abs(supplier.lead_time_days - quote.production_lead_time_days)
            if diff > LEAD_TIME_TOLERANCE_DAYS:
                conflicts.append(Conflict(
                    sid, "lead_time_days",
                    supplier.lead_time_days, quote.production_lead_time_days,
                    f"Profile lead time ({supplier.lead_time_days}d) disagrees with "
                    f"quotation lead time ({quote.production_lead_time_days}d) by {diff}d. "
                    f"Do not treat either as verified — flag for human review.",
                ))

        if supplier.min_order_quantity is not None:
            if abs(supplier.min_order_quantity - quote.minimum_order_quantity) > MOQ_TOLERANCE:
                conflicts.append(Conflict(
                    sid, "min_order_quantity",
                    supplier.min_order_quantity, quote.minimum_order_quantity,
                    f"Profile MOQ ({supplier.min_order_quantity}) differs from quotation MOQ "
                    f"({quote.minimum_order_quantity}).",
                ))
    return conflicts
