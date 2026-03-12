"""
Request/response types for tools to avoid schema mismatch (plan: tools/schemas.py).
"""
from typing import Any

from pydantic import BaseModel, Field


# --- Tool A: get_weather ---
class GetWeatherOutput(BaseModel):
    forecast_summary: str
    rain_probability: float
    severe_alert: bool


# --- Tool B: search_hotels ---
class HotelItem(BaseModel):
    name: str
    price_per_night: float
    rating: float
    availability: bool


class SearchHotelsOutput(BaseModel):
    hotels: list[HotelItem] = Field(default_factory=list)


# --- Tool C: estimate_transport ---
class TransportOption(BaseModel):
    mode: str
    price_min: float
    price_max: float
    duration_hours: float


class EstimateTransportOutput(BaseModel):
    options: list[TransportOption] = Field(default_factory=list)


# --- Tool D: calculate_budget ---
class BudgetLineItem(BaseModel):
    amount: float
    label: str = ""


class CalculateBudgetOutput(BaseModel):
    subtotal: float
    tax_fee: float
    total: float
    assumptions: list[str] = Field(default_factory=list)


# --- Tool E: risk_policy_advisor ---
class RiskPolicyOutput(BaseModel):
    risk_level: str
    fallback_plan: str
    warnings: list[str] = Field(default_factory=list)


# --- Tool F: currency_fx ---
class CurrencyFxOutput(BaseModel):
    base: str
    quote: str
    rate: float
    as_of: str = ""


# --- Tool G: human_approval ---
class HumanApprovalOutput(BaseModel):
    status: str  # "pending" | "approved" | "rejected"
    message: str = ""
