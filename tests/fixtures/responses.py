"""
Mock tool responses per scenario (for patching in tests).
"""
import json

# Scenario 1 - Happy path
HAPPY_WEATHER = json.dumps({
    "forecast_summary": "Sunny, 28-32°C",
    "rain_probability": 0.1,
    "severe_alert": False,
})

HAPPY_HOTELS = json.dumps({
    "hotels": [
        {"name": "Hotel A", "price_per_night": 500000, "rating": 4.2, "availability": True},
        {"name": "Hotel B", "price_per_night": 700000, "rating": 4.5, "availability": True},
    ]
})

HAPPY_TRANSPORT = json.dumps({
    "options": [
        {"mode": "flight", "price_min": 1500000, "price_max": 2500000, "duration_hours": 1.5},
        {"mode": "train", "price_min": 800000, "price_max": 1200000, "duration_hours": 16},
    ]
})

# Scenario 2 - Severe rain (re-plan)
SEVERE_RAIN_WEATHER = json.dumps({
    "forecast_summary": "Heavy rain, possible flood",
    "rain_probability": 0.95,
    "severe_alert": True,
})

# Scenario 3 - Hotel search empty
HOTELS_EMPTY = json.dumps({"hotels": []})

# Scenario 4 - Transport timeout (fallback message)
TRANSPORT_TIMEOUT_FALLBACK = json.dumps({
    "options": [],
    "fallback": "Transport API timeout; use approximate budget 2,000,000 VND for transport.",
})

# Scenario 5 - Conflicting prices (malformed string price)
MALFORMED_PRICE_HOTELS = json.dumps({
    "hotels": [
        {"name": "Hotel X", "price_per_night": "1.200.000", "rating": 4.0, "availability": True},
    ]
})

# Scenario 7 - Approval: human_approval returns pending
HUMAN_APPROVAL_PENDING = json.dumps({
    "status": "pending",
    "message": "Approval required for action.",
})

# Scenario 8 - Loop trap: malformed weather twice
MALFORMED_WEATHER = json.dumps({"invalid": "no forecast_summary"})

# Scenario 9 - Hallucination: tool disabled / error
TOOL_ERROR = "Tool temporarily unavailable."

# Scenario 10 - Parallel: delayed / conflicting (same as conflict for simplicity)
CONFLICTING_BUDGET = json.dumps({
    "subtotal": 1000000,
    "tax_fee": 100000,
    "total": 5000000,  # inconsistent
    "assumptions": [],
})
