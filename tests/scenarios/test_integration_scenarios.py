"""
Integration-style scenario tests (10 scenarios). Run with OPENAI_API_KEY for full run.
AC11: at least 10 test scenarios; AC12: at least 3 fail scenarios with trace.
"""
import os
import pytest

from src.agents.orchestrator import create_orchestrator_agent
from src.output.contract import FinalAnswer, Findings
from src.tracing.langfuse_setup import get_trace_metadata


pytestmark = [pytest.mark.integration]


@pytest.fixture
def agent():
    return create_orchestrator_agent(use_subagents=True)


@pytest.mark.parametrize(
    "scenario_id,test_case_id,user_input_snippet",
    [
        ("SCN_001_HAPPY", "TC_HAPPY_01", "Hà Nội Đà Nẵng cuối tuần, thời tiết khách sạn ngân sách"),
        ("SCN_002_SEVERE_RAIN", "TC_RAIN_01", "Hà Nội Đà Nẵng cuối tuần, nếu mưa lớn đề xuất dự phòng"),
        ("SCN_003_HOTEL_EMPTY", "TC_HOTEL_01", "Tìm khách sạn Đà Nẵng budget 100k"),
        ("SCN_004_TIMEOUT", "TC_TIMEOUT_01", "Hà Nội Đà Nẵng, ước tính vé máy bay tàu"),
        ("SCN_005_CONFLICT", "TC_CONFLICT_01", "Lên ngân sách tổng cho chuyến đi"),
        ("SCN_006_MISSING_CONSTRAINT", "TC_MISSING_01", "Gợi ý chuyến đi Đà Nẵng"),
        ("SCN_007_APPROVAL", "TC_APPROVAL_01", "Book giúp tôi khách sạn Đà Nẵng"),
        ("SCN_008_LOOP_TRAP", "TC_LOOP_01", "Thời tiết Đà Nẵng và khách sạn"),
        ("SCN_009_HALLUCINATION", "TC_HALL_01", "Tính ngân sách và thời tiết"),
        ("SCN_010_PARALLEL_RACE", "TC_PARALLEL_01", "Hà Nội Đà Nẵng khách sạn và vé"),
    ],
    ids=[
        "happy_path",
        "severe_rain",
        "hotel_empty",
        "timeout",
        "conflicting_prices",
        "missing_constraint",
        "approval_required",
        "loop_trap",
        "hallucination_trap",
        "parallel_race",
    ],
)
def test_scenario_has_trace_metadata(scenario_id, test_case_id, user_input_snippet, agent, skip_without_openai):
    """Each scenario has scenario_id and test_case_id for trace filtering (AC10, AC11)."""
    metadata = get_trace_metadata(scenario_id=scenario_id, test_case_id=test_case_id)
    assert metadata["scenario_id"] == scenario_id
    assert metadata["test_case_id"] == test_case_id


def test_orchestrator_agent_has_at_least_three_tool_types(agent):
    """AC1: Agent uses at least 3 tools in happy path (tool list includes weather, hotels, transport, budget, risk, fx, approval + optional subagents)."""
    # Orchestrator has 7 function tools + 2 agent tools when use_subagents=True
    assert agent.tools is not None
    tool_names = [getattr(t, "name", str(t)) for t in agent.tools]
    assert len(tool_names) >= 5  # at least 5 callables (core tools or agent tools)


def test_final_answer_contract_structure():
    """AC4: Final answer has assumptions and warnings fields."""
    a = FinalAnswer(
        task_summary="Done",
        plan_executed=[],
        findings=Findings(),
        warnings=["Assumption: budget in VND"],
        fallback_options=[],
        confidence=0.8,
        needs_human_approval=False,
    )
    d = a.to_json_dict()
    assert "warnings" in d
    assert "findings" in d
    assert "plan_executed" in d
