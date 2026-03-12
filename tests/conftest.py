"""
Pytest config and shared fixtures for TravelOps scenarios.
"""
import os
import pytest

# Use stub tools during tests (no real API calls)
os.environ.setdefault("TRAVELOPS_USE_REAL_API", "0")


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: mark test as integration (needs OPENAI_API_KEY)")
    config.addinivalue_line("markers", "failure_mode: mark test as failure-mode scenario (trace should show cause)")


@pytest.fixture
def scenario_ids():
    """Scenario IDs for trace filtering (AC10)."""
    return {
        "happy": "SCN_001_HAPPY",
        "severe_rain": "SCN_002_SEVERE_RAIN",
        "hotel_empty": "SCN_003_HOTEL_EMPTY",
        "transport_timeout": "SCN_004_TIMEOUT",
        "conflicting_prices": "SCN_005_CONFLICT",
        "missing_constraint": "SCN_006_MISSING_CONSTRAINT",
        "approval_required": "SCN_007_APPROVAL",
        "loop_trap": "SCN_008_LOOP_TRAP",
        "hallucination_trap": "SCN_009_HALLUCINATION",
        "parallel_race": "SCN_010_PARALLEL_RACE",
    }


@pytest.fixture
def skip_without_openai():
    """Skip test if OPENAI_API_KEY is not set (integration tests)."""
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set; integration test skipped")
