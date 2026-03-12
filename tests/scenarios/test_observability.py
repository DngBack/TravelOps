"""
Group D — Trace observability: trace metadata, span metadata helpers.
"""
import pytest

from src.tracing.langfuse_setup import (
    get_trace_metadata,
    get_span_metadata,
)


class TestTraceMetadata:
    """AC5, AC10: root trace metadata for filtering."""

    def test_trace_metadata_has_app_and_env(self):
        m = get_trace_metadata()
        assert m["app"] == "travel_ops_agent"
        assert "env" in m

    def test_trace_metadata_accepts_scenario_and_test_case(self):
        m = get_trace_metadata(scenario_id="SCN_004_TIMEOUT", test_case_id="TC_TOOL_017")
        assert m["scenario_id"] == "SCN_004_TIMEOUT"
        assert m["test_case_id"] == "TC_TOOL_017"

    def test_trace_metadata_has_versions(self):
        m = get_trace_metadata(agent_version="0.1.0", prompt_version="plan-v3", toolset_version="tools-v2")
        assert m["agent_version"] == "0.1.0"
        assert m["prompt_version"] == "plan-v3"
        assert m["toolset_version"] == "tools-v2"


class TestSpanMetadata:
    """Span-level metadata for status, retry, error_type, etc."""

    def test_span_metadata_status_and_retry(self):
        m = get_span_metadata(status="error", retry_count=2)
        assert m["status"] == "error"
        assert m["retry_count"] == 2

    def test_span_metadata_tool_name_and_fallback(self):
        m = get_span_metadata(tool_name="get_weather", fallback_used=True)
        assert m["tool_name"] == "get_weather"
        assert m["fallback_used"] is True

    def test_span_metadata_error_type_and_severity(self):
        m = get_span_metadata(error_type="timeout", severity="high")
        assert m["error_type"] == "timeout"
        assert m["severity"] == "high"
