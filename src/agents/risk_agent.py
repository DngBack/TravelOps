"""
RiskAgent: evaluates risk, fallback plans, and detects inconsistencies.
Used as agent-as-tool or handoff by TripOrchestrator (M3).
"""
from agents import Agent

from src.tools.core import risk_policy_advisor


RISK_INSTRUCTIONS = """
You are a risk and policy advisor for travel. Your job is to:
1. Use risk_policy_advisor with the provided weather summary, budget summary, and constraints.
2. Interpret the result and highlight risk_level, fallback_plan, and warnings.
3. If you detect inconsistencies (e.g. budget total does not match components), note them.
4. Return a short structured summary suitable for the orchestrator to include in the final answer.
"""


def create_risk_agent() -> Agent:
    return Agent(
        name="RiskAgent",
        instructions=RISK_INSTRUCTIONS,
        tools=[risk_policy_advisor],
    )
