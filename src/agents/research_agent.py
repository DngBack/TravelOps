"""
ResearchAgent: gathers weather, hotels, transport; normalizes data.
Used as agent-as-tool or handoff by TripOrchestrator (M3).
"""
from agents import Agent

from src.tools.core import get_weather, search_hotels, estimate_transport


RESEARCH_INSTRUCTIONS = """
You are a research specialist for trip planning. Your job is to:
1. Call get_weather, search_hotels, and estimate_transport with the parameters provided.
2. Normalize and summarize the results (dates, prices, availability).
3. Return a concise structured summary. Do not guess or invent data; only report what the tools return.
4. If a tool returns empty or errors, say so clearly in your summary.
"""


def create_research_agent() -> Agent:
    return Agent(
        name="ResearchAgent",
        instructions=RESEARCH_INSTRUCTIONS,
        tools=[get_weather, search_hotels, estimate_transport],
    )
