"""
Final answer contract: JSON structure + NL summary for TravelOps agent.
"""
from typing import Any

from pydantic import BaseModel, Field


class WeatherFinding(BaseModel):
    forecast_summary: str = ""
    rain_probability: float = 0.0
    severe_alert: bool = False


class LodgingItem(BaseModel):
    name: str = ""
    price_per_night: float = 0.0
    rating: float = 0.0
    availability: bool = True


class TransportItem(BaseModel):
    mode: str = ""
    price_range_min: float = 0.0
    price_range_max: float = 0.0
    duration_hours: float = 0.0


class BudgetFinding(BaseModel):
    subtotal: float = 0.0
    tax_fee: float = 0.0
    total: float = 0.0
    assumptions: list[str] = Field(default_factory=list)


class RiskFinding(BaseModel):
    risk_level: str = ""
    fallback_plan: str = ""
    warnings: list[str] = Field(default_factory=list)


class Findings(BaseModel):
    weather: dict[str, Any] = Field(default_factory=dict)
    lodging: list[dict[str, Any]] = Field(default_factory=list)
    transport: list[dict[str, Any]] = Field(default_factory=list)
    budget: dict[str, Any] = Field(default_factory=dict)
    risk: dict[str, Any] = Field(default_factory=dict)


class FinalAnswer(BaseModel):
    """Structured final answer per spec."""

    task_summary: str = ""
    plan_executed: list[str] = Field(default_factory=list)
    findings: Findings = Field(default_factory=Findings)
    warnings: list[str] = Field(default_factory=list)
    fallback_options: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    needs_human_approval: bool = False

    def to_json_dict(self) -> dict[str, Any]:
        return self.model_dump()

    def to_nl_summary(self) -> str:
        parts = [self.task_summary]
        if self.warnings:
            parts.append("Warnings: " + "; ".join(self.warnings))
        if self.fallback_options:
            parts.append("Fallbacks: " + "; ".join(self.fallback_options))
        if self.needs_human_approval:
            parts.append("This request needs human approval before proceeding.")
        return "\n".join(parts)


def findings_to_dict(findings: Findings) -> dict[str, Any]:
    return findings.model_dump()
