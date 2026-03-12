"""
TripOrchestratorAgent: plan, tool selection, re-plan rules, approval stop, final answer contract.
Supports M1 (tools only) and M3 (with ResearchAgent + RiskAgent as tools).
"""
from agents import Agent

from src.tools.core import (
    get_weather,
    search_hotels,
    estimate_transport,
    calculate_budget,
    risk_policy_advisor,
    currency_fx,
    human_approval,
    web_search,
)
from src.agents.research_agent import create_research_agent
from src.agents.risk_agent import create_risk_agent


ORCHESTRATOR_INSTRUCTIONS = """
You are the TripOrchestrator for travel planning (e.g. Hanoi -> Da Nang weekend).

You MUST:
1. **Create an explicit plan first** (plan node): list the steps you will take (weather, hotels, transport, budget, risk).
2. **Use tools** — never guess or invent. Call get_weather, search_hotels, estimate_transport, calculate_budget, risk_policy_advisor; or web_search for live/extra info (e.g. "hotels Da Nang", "flight Hanoi Da Nang price"). Prefer dedicated tools when available; use web_search when you need Google/live results.
3. **Re-plan when**:
   - Weather returns severe_alert = true (suggest indoor or change dates).
   - Hotel search returns empty (widen budget or area).
   - Transport cost exceeds budget (suggest alternatives).
   - Two tools give conflicting data (note and adjust).
   - A tool times out (retry once, then fallback with a warning).
4. **Approval gate**: If the user asks to "book", "pay", "send email", or any real-world action, call human_approval and STOP. Do not proceed until approved. Set needs_human_approval in your final answer.
5. **Final answer** must be structured:
   - task_summary: short summary
   - plan_executed: list of steps you actually did
   - findings: { weather, lodging, transport, budget, risk } (from tool outputs)
   - warnings: any caveats or inconsistencies
   - fallback_options: if you re-planned, list alternatives
   - confidence: 0–1
   - needs_human_approval: true if you stopped for approval

Use currency_fx only when user needs conversion. You may use web_search to look up current prices, hotels, or weather if other tools are unavailable or you need additional sources.
"""


def create_orchestrator_agent(
    use_subagents: bool = True,
    model: str | None = None,
) -> Agent:
    """
    Create TripOrchestrator. model: tên model (instant vs thinking); None = lấy từ config.
    """
    if model is None:
        from src.config import get_model_for_mode
        model = get_model_for_mode()
    research = create_research_agent(model=model)
    risk = create_risk_agent(model=model)

    tools = [
        get_weather,
        search_hotels,
        estimate_transport,
        calculate_budget,
        risk_policy_advisor,
        currency_fx,
        human_approval,
        web_search,
    ]
    if use_subagents:
        tools.extend([
            research.as_tool(
                tool_name="research_tool",
                tool_description="Delegate weather, hotel, and transport research. Provide destination, dates, budget.",
            ),
            risk.as_tool(
                tool_name="risk_tool",
                tool_description="Delegate risk assessment. Provide weather summary, budget summary, constraints.",
            ),
        ])

    return Agent(
        name="TripOrchestrator",
        instructions=ORCHESTRATOR_INSTRUCTIONS,
        tools=tools,
        model=model,
    )
