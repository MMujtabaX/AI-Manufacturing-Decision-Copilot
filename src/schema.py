"""Pydantic schemas for the Manufacturing Decision Copilot.

Explicit schemas make eligibility/ranking auditable and give the LLM
extraction layer a strict contract to fill in (source, confidence, etc.)
instead of returning free text judges can't verify.
"""
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


class ProductRequirement(BaseModel):
    product_name: str
    mandatory_certifications: List[str] = Field(default_factory=list)
    min_order_quantity_max: Optional[int] = None  # supplier's MOQ must be <= this
    max_lead_time_days: Optional[int] = None
    preferred_locations: List[str] = Field(default_factory=list)
    target_unit_price: Optional[float] = None
    min_quality_history_score: Optional[float] = None  # 0-1
    min_sustainability_score: Optional[float] = None  # 0-1


class Supplier(BaseModel):
    supplier_id: str
    name: str
    location: str
    certifications: List[str] = Field(default_factory=list)
    min_order_quantity: Optional[int] = None
    capacity_units_per_month: Optional[int] = None
    quality_history_score: Optional[float] = None  # 0-1, from historical performance data
    lead_time_days: Optional[int] = None
    sustainability_score: Optional[float] = None  # 0-1
    notes: Optional[str] = None  # free text - candidate for LLM extraction


class Quotation(BaseModel):
    supplier_id: str
    unit_price: float
    currency: str
    tooling_cost: float = 0.0
    minimum_order_quantity: int
    payment_terms: str
    production_lead_time_days: int
    freight_cost_per_unit: float = 0.0
    duty_rate_pct: float = 0.0
    incoterm: str
    quote_date: str
    notes: Optional[str] = None


class ExtractedFact(BaseModel):
    """Structured output from the LLM normalization layer. Every fact must
    trace back to a specific source snippet, per the brief's evidence-citation
    and anti-hallucination requirements."""
    supplier_id: str
    field: str
    value: str
    source_snippet: str
    confidence: float  # 0-1
    abstained: bool = False


class EligibilityResult(BaseModel):
    supplier_id: str
    eligible: bool
    reasons: List[str]  # human-readable, tied to specific requirement fields


class RankedSupplier(BaseModel):
    supplier_id: str
    name: str
    score: float
    rank: int
    score_breakdown: dict
    explanation: str
