"""
Langfuse + OpenInference instrumentation for TravelOps.
- Instrument OpenAI Agents so LLM/tool/handoff spans export to Langfuse via OTel.
- Helpers for trace metadata (scenario_id, test_case_id, etc.) and custom span names.
"""
import os
from typing import Any

_instrumented = False


def setup_tracing() -> None:
    """
    Call once at app startup. Instruments OpenAI Agents SDK so traces/spans
    are exported to Langfuse via OpenTelemetry/OpenInference.
    """
    global _instrumented
    if _instrumented:
        return
    try:
        from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor

        OpenAIAgentsInstrumentor().instrument()
        _instrumented = True
    except ImportError:
        pass


def get_trace_metadata(
    *,
    scenario_id: str | None = None,
    test_case_id: str | None = None,
    user_role: str = "tester",
    agent_version: str | None = None,
    prompt_version: str | None = None,
    toolset_version: str | None = None,
) -> dict[str, Any]:
    """
    Build root trace metadata for Langfuse (AC5, AC10).
    Attach via propagate_attributes(metadata=...) when calling Runner.run.
    """
    return {
        "app": "travel_ops_agent",
        "env": os.environ.get("TRAVELOPS_ENV", "staging"),
        "scenario_id": scenario_id or "",
        "test_case_id": test_case_id or "",
        "user_role": user_role,
        "agent_version": agent_version or os.environ.get("TRAVELOPS_AGENT_VERSION", "0.1.0"),
        "prompt_version": prompt_version or "plan-v3",
        "toolset_version": toolset_version or "tools-v2",
    }


def get_span_metadata(
    *,
    status: str = "success",
    latency_ms: float | None = None,
    retry_count: int = 0,
    error_type: str | None = None,
    degraded_mode: bool = False,
    tool_name: str | None = None,
    plan_step_id: str | None = None,
    fallback_used: bool = False,
    severity: str | None = None,
) -> dict[str, Any]:
    """
    Build span-level metadata for custom or tool spans (planning, replan, final_synthesis).
    """
    m: dict[str, Any] = {
        "status": status,
        "retry_count": retry_count,
        "degraded_mode": degraded_mode,
    }
    if latency_ms is not None:
        m["latency_ms"] = latency_ms
    if error_type:
        m["error_type"] = error_type
    if tool_name:
        m["tool_name"] = tool_name
    if plan_step_id:
        m["plan_step_id"] = plan_step_id
    if fallback_used:
        m["fallback_used"] = True
    if severity:
        m["severity"] = severity
    return m
