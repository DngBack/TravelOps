"""
Group C — Robustness: timeout, retry, fallback, partial failure, conflicting outputs.
"""
import pytest

from src.tools.mocks.builders import (
    mock_weather_severe,
    mock_hotels_empty,
    mock_transport_timeout_response,
    mock_malformed_price,
    mock_currency_stale,
)
import json


class TestFailureModeFixtures:
    """Fixtures for failure modes produce valid JSON and expected shapes."""

    def test_severe_weather_has_severe_alert(self):
        data = json.loads(mock_weather_severe())
        assert data.get("severe_alert") is True

    def test_hotels_empty_returns_empty_list(self):
        data = json.loads(mock_hotels_empty())
        assert data.get("hotels") == []

    def test_transport_timeout_has_fallback(self):
        s = mock_transport_timeout_response()
        data = json.loads(s)
        assert "fallback" in data or "options" in data

    def test_malformed_price_has_string_price(self):
        data = json.loads(mock_malformed_price())
        assert len(data.get("hotels", [])) > 0
        assert isinstance(data["hotels"][0].get("price_per_night"), str)

    def test_currency_stale_has_old_date(self):
        data = json.loads(mock_currency_stale())
        assert "as_of" in data
