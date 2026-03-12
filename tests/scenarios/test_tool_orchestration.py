"""
Group B — Tool orchestration: correct tool choice, correct params, handle empty/malformed output.
"""
import pytest

from src.tools.schemas import (
    GetWeatherOutput,
    SearchHotelsOutput,
    CalculateBudgetOutput,
    RiskPolicyOutput,
    HumanApprovalOutput,
)
from src.output.contract import FinalAnswer, Findings


class TestToolSchemas:
    """Schema validation to avoid mismatch (plan: schema mismatch failure mode)."""

    def test_weather_output_schema(self):
        o = GetWeatherOutput(forecast_summary="Sunny", rain_probability=0.2, severe_alert=False)
        assert o.rain_probability == 0.2
        assert o.severe_alert is False

    def test_search_hotels_output_schema(self):
        o = SearchHotelsOutput(hotels=[])
        assert o.hotels == []
        o2 = SearchHotelsOutput(hotels=[{"name": "A", "price_per_night": 500, "rating": 4.0, "availability": True}])
        assert len(o2.hotels) == 1
        assert o2.hotels[0].price_per_night == 500

    def test_calculate_budget_output_schema(self):
        o = CalculateBudgetOutput(subtotal=1000, tax_fee=100, total=1100, assumptions=[])
        assert o.total == 1100

    def test_risk_policy_output_schema(self):
        o = RiskPolicyOutput(risk_level="low", fallback_plan="Indoor options", warnings=[])
        assert o.risk_level == "low"

    def test_human_approval_output_schema(self):
        o = HumanApprovalOutput(status="pending", message="Need approval")
        assert o.status == "pending"


class TestOutputContract:
    """Final answer structure (AC4)."""

    def test_final_answer_has_required_fields(self):
        a = FinalAnswer(
            task_summary="Trip planned",
            plan_executed=["Checked weather", "Searched hotels"],
            findings=Findings(),
            warnings=[],
            fallback_options=[],
            confidence=0.9,
            needs_human_approval=False,
        )
        d = a.to_json_dict()
        assert "task_summary" in d
        assert "plan_executed" in d
        assert "findings" in d
        assert "warnings" in d
        assert "fallback_options" in d
        assert "confidence" in d
        assert "needs_human_approval" in d

    def test_final_answer_nl_summary_includes_warnings(self):
        a = FinalAnswer(task_summary="Done", warnings=["Heavy rain possible"])
        s = a.to_nl_summary()
        assert "Warnings" in s
        assert "Heavy rain" in s
