import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.schema import Supplier, Quotation
from src.conflicts import detect_conflicts


def _q(sid, lead, moq):
    return Quotation(supplier_id=sid, unit_price=1.0, currency="USD",
                     minimum_order_quantity=moq, payment_terms="net30",
                     production_lead_time_days=lead, incoterm="FOB", quote_date="2026-01-01")


def test_detects_lead_time_conflict():
    suppliers = {"A": Supplier(supplier_id="A", name="A", location="X",
                               lead_time_days=28, min_order_quantity=1000)}
    quotations = {"A": _q("A", lead=45, moq=1000)}
    conflicts = detect_conflicts(suppliers, quotations)
    assert any(c.field == "lead_time_days" for c in conflicts)


def test_no_conflict_when_aligned():
    suppliers = {"A": Supplier(supplier_id="A", name="A", location="X",
                               lead_time_days=30, min_order_quantity=1000)}
    quotations = {"A": _q("A", lead=30, moq=1000)}
    conflicts = detect_conflicts(suppliers, quotations)
    assert conflicts == []
