"""
Mock tool responses for test scenarios (timeout, empty, malformed, conflict).
Tests can patch tool implementations or use these builders.
"""
from src.tools.mocks.builders import (
    mock_weather_severe,
    mock_hotels_empty,
    mock_transport_timeout_response,
    mock_malformed_price,
    mock_currency_stale,
)

__all__ = [
    "mock_weather_severe",
    "mock_hotels_empty",
    "mock_transport_timeout_response",
    "mock_malformed_price",
    "mock_currency_stale",
]
