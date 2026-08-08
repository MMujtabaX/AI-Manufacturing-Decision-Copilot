import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.schema import ProductRequirement, Supplier
from src.rules import check_eligibility


def make_req(**overrides):
    base = dict(
        product_name="Test product",
        mandatory_certifications=["ISO9001"],
        min_order_quantity_max=1000,
        max_lead_time_days=30,
    )
    base.update(overrides)
    return ProductRequirement(**base)


def make_supplier(**overrides):
    base = dict(
        supplier_id="X1", name="Test Supplier", location="Vietnam",
        certifications=["ISO9001"], min_order_quantity=500, lead_time_days=20,
    )
    base.update(overrides)
    return Supplier(**base)


def test_passes_all_constraints():
    result = check_eligibility(make_req(), make_supplier())
    assert result.eligible is True


def test_fails_missing_certification():
    result = check_eligibility(make_req(), make_supplier(certifications=[]))
    assert result.eligible is False
    assert "certification" in result.reasons[0].lower()


def test_fails_moq_too_high():
    result = check_eligibility(make_req(), make_supplier(min_order_quantity=5000))
    assert result.eligible is False


def test_fails_lead_time_too_long():
    result = check_eligibility(make_req(), make_supplier(lead_time_days=90))
    assert result.eligible is False
