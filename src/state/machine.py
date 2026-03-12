"""
State machine for TravelOps workflow.
States and transition rules per plan; re-plan triggers for tester observability.
"""
from enum import Enum
from typing import Any


class WorkflowState(str, Enum):
    RECEIVED = "RECEIVED"
    PLANNING = "PLANNING"
    RESEARCHING = "RESEARCHING"
    REPLANNING = "REPLANNING"
    RISK_REVIEW = "RISK_REVIEW"
    FINALIZING = "FINALIZING"
    FAILED = "FAILED"
    NEEDS_APPROVAL = "NEEDS_APPROVAL"


# Transition rules (for documentation and optional runtime checks)
TRANSITIONS = {
    WorkflowState.RECEIVED: [WorkflowState.PLANNING],
    WorkflowState.PLANNING: [WorkflowState.RESEARCHING],
    WorkflowState.RESEARCHING: [WorkflowState.REPLANNING, WorkflowState.RISK_REVIEW, WorkflowState.FAILED],
    WorkflowState.REPLANNING: [WorkflowState.RESEARCHING],
    WorkflowState.RISK_REVIEW: [WorkflowState.NEEDS_APPROVAL, WorkflowState.FINALIZING, WorkflowState.FAILED],
    WorkflowState.NEEDS_APPROVAL: [WorkflowState.FINALIZING],
    WorkflowState.FINALIZING: [],
    WorkflowState.FAILED: [],
}


def should_replan(
    *,
    weather_severe_alert: bool = False,
    hotel_search_empty: bool = False,
    transport_exceeds_budget: bool = False,
    tools_conflict: bool = False,
    tool_timeout: bool = False,
) -> bool:
    """
    Re-plan trigger: return True if any condition warrants re-planning.
    Used by orchestrator instructions and optional code checks.
    """
    return (
        weather_severe_alert
        or hotel_search_empty
        or transport_exceeds_budget
        or tools_conflict
        or tool_timeout
    )


def get_next_states(current: WorkflowState) -> list[WorkflowState]:
    """Return allowed next states for current state."""
    return list(TRANSITIONS.get(current, []))
