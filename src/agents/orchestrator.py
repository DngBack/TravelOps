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
2. **Use tools** — never guess or invent. Call get_weather, search_hotels, estimate_transport, calculate_budget, risk_policy_advisor; use **research_tool** when you need deeper multi-step research (it can chain web_search). Use **web_search** yourself for targeted follow-ups (hotel names, flight deals, reviews). Prefer dedicated tools first; add web_search (search_depth="advanced" when needed) when results are thin.
3. **Quality bar for findings** (do not accept shallow output):
   - **Lodging**: Final answer must list **at least several specific hotel or resort names** (from tool/snippet data), each with **link** and short **snippet** when available. If search_hotels only returned OTA city pages, you MUST run extra web_search queries for concrete properties or delegate research_tool again with narrower instructions.
   - **Transport**: Include **booking_links** from estimate_transport JSON (Skyscanner, DSĐV, airline search, etc.) in the final answer — not only price ranges.
4. **Re-plan when**:
   - Weather returns severe_alert = true (suggest indoor or change dates).
   - Hotel search returns empty or only generic portals (widen queries, repeat search, or different angles).
   - Transport cost exceeds budget (suggest alternatives).
   - Two tools give conflicting data (note and adjust).
   - A tool times out (retry once, then fallback with a warning).
5. **Approval gate**: If the user asks to "book", "pay", "send email", or any real-world action, call human_approval and STOP. Do not proceed until approved. Set needs_human_approval in your final answer.
6. **Final answer** must be structured:
   - task_summary: short summary
   - plan_executed: list of steps you actually did (including any extra searches)
   - findings: { weather, lodging, transport, budget, risk } — **grounded in tool outputs**
   - warnings: e.g. "prices indicative", "verify on booking site"
   - fallback_options: if you re-planned, list alternatives
   - confidence: 0–1
   - needs_human_approval: true if you stopped for approval

Use currency_fx only when user needs conversion.
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
