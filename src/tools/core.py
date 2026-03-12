"""
Seven TravelOps tools: A–E (core) + F currency_fx (failure-prone) + G human_approval (approval gate).
Use real APIs when configured; fallback to stub on error or missing key.
"""
import json
import os
from typing import Any

from agents import function_tool

from src.tools.schemas import (
    BudgetLineItem,
    CalculateBudgetOutput,
    CurrencyFxOutput,
    EstimateTransportOutput,
    GetWeatherOutput,
    HumanApprovalOutput,
    RiskPolicyOutput,
    SearchHotelsOutput,
    HotelItem,
    TransportOption,
)


def _to_str(data: Any) -> str:
    """Serialize tool output to string for LLM consumption."""
    if isinstance(data, (dict, list)):
        return json.dumps(data, ensure_ascii=False)
    if hasattr(data, "model_dump"):
        return json.dumps(data.model_dump(), ensure_ascii=False)
    return str(data)


def _use_real_api() -> bool:
    """Use real APIs (no stub) when env requests it."""
    return os.environ.get("TRAVELOPS_USE_REAL_API", "1").strip().lower() in ("1", "true", "yes")


# --- Tool A: get_weather (Open-Meteo, no key) ---
@function_tool
def get_weather(destination: str, dates: str) -> str:
    """
    Get weather forecast for a destination and date range.
    Returns forecast summary, rain probability, and severe_alert (true if severe weather).
    Uses Open-Meteo API (real data, no API key). Falls back to stub on error.
    """
    if _use_real_api():
        from src.tools.api_clients import open_meteo_forecast
        out = open_meteo_forecast(destination, dates)
        if out is not None:
            return _to_str(out)
    out = GetWeatherOutput(
        forecast_summary="Partly cloudy, 25-30°C",
        rain_probability=0.2,
        severe_alert=False,
    )
    return _to_str(out)


# --- Tool B: search_hotels (Amadeus or HotelsAPI.com) ---
@function_tool
def search_hotels(
    destination: str,
    checkin: str,
    checkout: str,
    budget: float,
) -> str:
    """
    Search hotels at destination for checkin/checkout dates within budget.
    Returns list of hotels with name, price_per_night, rating, availability.
    Uses Amadeus when AMADEUS_CLIENT_ID+SECRET set; else HotelsAPI.com when HOTELS_API_KEY set.
    """
    if _use_real_api():
        if os.environ.get("AMADEUS_CLIENT_ID"):
            from src.tools.api_clients import amadeus_hotel_list
            result = amadeus_hotel_list(destination, budget)
            if result is not None:
                return _to_str(result)
        if os.environ.get("HOTELS_API_KEY"):
            from src.tools.api_clients import hotels_api_com_search
            result = hotels_api_com_search(destination, budget)
            if result is not None:
                return _to_str(result)
    out = SearchHotelsOutput(
        hotels=[
            HotelItem(name="Hotel A", price_per_night=500000, rating=4.2, availability=True),
            HotelItem(name="Hotel B", price_per_night=700000, rating=4.5, availability=True),
        ]
    )
    return _to_str(out)


# --- Tool C: estimate_transport (Amadeus or AviationStack) ---
@function_tool
def estimate_transport(origin: str, destination: str, dates: str) -> str:
    """
    Estimate transport options (flight/train/bus) between origin and destination for dates.
    Returns options with mode, price range (min/max), duration_hours.
    Uses Amadeus Flight Offers when AMADEUS_* set (has prices); else AviationStack routes when AVIATIONSTACK_ACCESS_KEY set (no prices).
    """
    if _use_real_api():
        if os.environ.get("AMADEUS_CLIENT_ID"):
            from src.tools.api_clients import amadeus_flight_offers
            options = amadeus_flight_offers(origin, destination, dates)
            if options:
                return _to_str(EstimateTransportOutput(options=options))
        if os.environ.get("AVIATIONSTACK_ACCESS_KEY"):
            from src.tools.api_clients import aviationstack_routes
            options = aviationstack_routes(origin, destination, dates)
            if options:
                return _to_str(EstimateTransportOutput(options=options))
    out = EstimateTransportOutput(
        options=[
            TransportOption(mode="flight", price_min=1500000, price_max=2500000, duration_hours=1.5),
            TransportOption(mode="train", price_min=800000, price_max=1200000, duration_hours=16),
        ]
    )
    return _to_str(out)


# --- Tool D: calculate_budget ---
@function_tool
def calculate_budget(items: list[BudgetLineItem]) -> str:
    """
    Calculate total budget from a list of line items (amount, label). Returns subtotal, tax/fee, total, assumptions.
    """
    subtotal = 0.0
    for it in items:
        if isinstance(it, BudgetLineItem):
            subtotal += it.amount
        elif isinstance(it, dict) and "amount" in it:
            val = it["amount"]
            if isinstance(val, (int, float)):
                subtotal += float(val)
            elif isinstance(val, str):
                try:
                    subtotal += float(val.replace(",", "").replace(".", "").strip() or 0)
                except ValueError:
                    pass
    tax_fee = subtotal * 0.1
    out = CalculateBudgetOutput(
        subtotal=subtotal,
        tax_fee=tax_fee,
        total=subtotal + tax_fee,
        assumptions=["Tax/fee 10% applied"],
    )
    return _to_str(out)


# --- Tool E: risk_policy_advisor (logic from inputs) ---
@function_tool
def risk_policy_advisor(
    weather: str,
    budget: str,
    constraints: str,
) -> str:
    """
    Evaluate risk given weather summary, budget summary, and user constraints.
    Returns risk_level, fallback_plan, warnings.
    Parses weather/budget text to set risk_level and fallback.
    """
    weather_lower = (weather or "").lower()
    severe = "severe" in weather_lower or "thunderstorm" in weather_lower or "severe_alert" in weather_lower
    if severe or "true" in weather_lower and "alert" in weather_lower:
        out = RiskPolicyOutput(
            risk_level="high",
            fallback_plan="Switch to indoor activities or change travel dates. Avoid outdoor exposure.",
            warnings=["Severe weather in forecast."],
        )
    else:
        out = RiskPolicyOutput(
            risk_level="low",
            fallback_plan="If weather worsens, consider indoor activities or shift dates.",
            warnings=[],
        )
    return _to_str(out)


# --- Tool F: currency_fx (Frankfurter API, no key) ---
@function_tool
def currency_fx(base: str, quote: str) -> str:
    """
    Get exchange rate from base to quote currency (e.g. USD, VND).
    Uses Frankfurter API (real rates, no API key). Falls back to stub on error.
    """
    if _use_real_api():
        from src.tools.api_clients import frankfurter_rate
        out = frankfurter_rate(base, quote)
        if out is not None:
            return _to_str(out)
    out = CurrencyFxOutput(base=base or "USD", quote=quote or "VND", rate=25000.0, as_of="")
    return _to_str(out)


# --- Tool G: human_approval (approval gate; never performs real book/email) ---
def _human_approval_impl(action: str, payload: str) -> str:
    """Implementation so tests can assert approval gate returns pending."""
    out = HumanApprovalOutput(
        status="pending",
        message=f"Approval required for action: {action}. Payload (summary): {payload[:200]}.",
    )
    return _to_str(out)


@function_tool
def human_approval(action: str, payload: str) -> str:
    """
    Request human approval for a sensitive action (e.g. book, send_email).
    Returns status: pending | approved | rejected. Call this when user asks to book or send email;
    do not proceed until approved.
    """
    return _human_approval_impl(action, payload)


# --- Tool H: web_search (DuckDuckGo only, no key) ---
@function_tool
def web_search(query: str, num_results: int = 5) -> str:
    """
    Search the web via DuckDuckGo (no API key). Use for current info: hotels, weather, flight prices, reviews.
    Pass a clear search query (e.g. "hotels in Da Nang Vietnam", "flight Hanoi to Da Nang price").
    Returns a list of results with title, link, snippet. Requires: pip install duckduckgo-search.
    """
    if not _use_real_api():
        return json.dumps({"results": [], "message": "Web search disabled (TRAVELOPS_USE_REAL_API=0)."})
    from src.tools.api_clients import web_search_results
    results = web_search_results(query, num_results)
    if not results:
        return json.dumps({"results": [], "message": "No results. Install duckduckgo-search: pip install duckduckgo-search"})
    return json.dumps({"results": results}, ensure_ascii=False)
