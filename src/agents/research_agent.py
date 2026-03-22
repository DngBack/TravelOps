"""
ResearchAgent: gathers weather, hotels, transport; normalizes data.
Used as agent-as-tool or handoff by TripOrchestrator (M3).
"""
from agents import Agent

from src.tools.core import estimate_transport, get_weather, search_hotels, web_search


RESEARCH_INSTRUCTIONS = """
You are a research specialist for trip planning. Be thorough — shallow summaries are not acceptable.

You MUST:
1. Call get_weather, search_hotels, and estimate_transport with accurate destination, dates, and budget.
2. After search_hotels, inspect the result:
   - If you mostly see **generic listing pages** (only city/OTA landing pages) or **few real hotel names**, run web_search 1–3 more times with **narrow queries**, e.g.
     "Hyatt Regency Danang review", "HAIAN Beach Hotel Da Nang", "khách sạn biển Mỹ Khê Đà Nẵng tên cụ thể".
   Use search_depth="advanced" when you need richer snippets.
3. For transport, read **booking_links** and **notes** in tool JSON; include those URLs in your summary so the user can open real booking/search pages.
4. Normalize and summarize: **named hotels** (not only portal links), **prices** if present, **rain/alert** from weather, **flight/train** options with links.
5. Do not invent prices or hotel names; only report tool/search outputs. If data is missing, say what is missing and what extra search you ran.
"""


def create_research_agent(model: str | None = None) -> Agent:
    if model is None:
        from src.config import get_model_for_mode
        model = get_model_for_mode()
    return Agent(
        name="ResearchAgent",
        instructions=RESEARCH_INSTRUCTIONS,
        tools=[get_weather, search_hotels, estimate_transport, web_search],
        model=model,
    )
