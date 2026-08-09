import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.schema import Supplier, Quotation
from src.rank import rank_suppliers, WEIGHT_PROFILES


def _sample():
    suppliers = {
        "A": Supplier(supplier_id="A", name="Cheap Slow", location="X",
                      lead_time_days=50, quality_history_score=0.7, sustainability_score=0.6),
        "B": Supplier(supplier_id="B", name="Pricey Fast", location="X",
                      lead_time_days=10, quality_history_score=0.9, sustainability_score=0.8),
    }
    quotations = {
        "A": Quotation(supplier_id="A", unit_price=1.0, currency="USD",
                        minimum_order_quantity=100, payment_terms="net30",
                        production_lead_time_days=50, incoterm="FOB", quote_date="2026-01-01"),
        "B": Quotation(supplier_id="B", unit_price=5.0, currency="USD",
                        minimum_order_quantity=100, payment_terms="net30",
                        production_lead_time_days=10, incoterm="FOB", quote_date="2026-01-01"),
    }
    return suppliers, quotations


def test_cost_focused_prefers_cheap_supplier():
    suppliers, quotations = _sample()
    ranked = rank_suppliers(["A", "B"], suppliers, quotations, "cost_focused")
    assert ranked[0].supplier_id == "A"


def test_speed_focused_prefers_fast_supplier():
    suppliers, quotations = _sample()
    ranked = rank_suppliers(["A", "B"], suppliers, quotations, "speed_focused")
    assert ranked[0].supplier_id == "B"


def test_all_profiles_produce_full_ranking():
    suppliers, quotations = _sample()
    for profile in WEIGHT_PROFILES:
        ranked = rank_suppliers(["A", "B"], suppliers, quotations, profile)
        assert len(ranked) == 2
        assert {r.rank for r in ranked} == {1, 2}
