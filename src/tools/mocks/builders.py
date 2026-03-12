"""
Build mock tool responses for failure-mode scenarios.
"""
import json


def mock_weather_severe() -> str:
    """Scenario 2: severe rain -> re-plan."""
    return json.dumps({
        "forecast_summary": "Heavy rain, possible flood",
        "rain_probability": 0.95,
        "severe_alert": True,
    })


def mock_hotels_empty() -> str:
    """Scenario 3: no hotels in budget."""
    return json.dumps({"hotels": []})


def mock_transport_timeout_response() -> str:
    """Scenario 4: after timeout/retry, return fallback message."""
    return json.dumps({
        "options": [],
        "fallback": "Transport API timeout; use approximate budget 2,000,000 VND for transport.",
    })


def mock_malformed_price() -> str:
    """Scenario 5: price as string with locale format."""
    return json.dumps({
        "hotels": [
            {"name": "Hotel X", "price_per_night": "1.200.000", "rating": 4.0, "availability": True},
        ]
    })


def mock_currency_stale() -> str:
    """Tool F failure: stale or wrong unit."""
    return json.dumps({
        "base": "USD",
        "quote": "VND",
        "rate": 23000.0,
        "as_of": "2020-01-01",
    })
