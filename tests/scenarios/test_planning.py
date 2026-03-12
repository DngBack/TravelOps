"""
Group A — Planning: agent creates plan, plan has required steps, re-plan when conditions change.
"""
import pytest

from src.state.machine import WorkflowState, should_replan, get_next_states, TRANSITIONS


class TestStateMachine:
    """State and transition rules."""

    def test_states_defined(self):
        assert WorkflowState.RECEIVED.value == "RECEIVED"
        assert WorkflowState.PLANNING.value == "PLANNING"
        assert WorkflowState.RESEARCHING.value == "RESEARCHING"
        assert WorkflowState.REPLANNING.value == "REPLANNING"
        assert WorkflowState.RISK_REVIEW.value == "RISK_REVIEW"
        assert WorkflowState.FINALIZING.value == "FINALIZING"
        assert WorkflowState.FAILED.value == "FAILED"
        assert WorkflowState.NEEDS_APPROVAL.value == "NEEDS_APPROVAL"

    def test_transitions_received_to_planning(self):
        next_states = get_next_states(WorkflowState.RECEIVED)
        assert WorkflowState.PLANNING in next_states

    def test_transitions_planning_to_researching(self):
        next_states = get_next_states(WorkflowState.PLANNING)
        assert WorkflowState.RESEARCHING in next_states

    def test_transitions_researching_can_replan_or_risk_review(self):
        next_states = get_next_states(WorkflowState.RESEARCHING)
        assert WorkflowState.REPLANNING in next_states
        assert WorkflowState.RISK_REVIEW in next_states

    def test_replan_triggers_severe_weather(self):
        assert should_replan(weather_severe_alert=True) is True

    def test_replan_triggers_hotel_empty(self):
        assert should_replan(hotel_search_empty=True) is True

    def test_replan_triggers_transport_over_budget(self):
        assert should_replan(transport_exceeds_budget=True) is True

    def test_replan_triggers_tools_conflict(self):
        assert should_replan(tools_conflict=True) is True

    def test_replan_triggers_timeout(self):
        assert should_replan(tool_timeout=True) is True

    def test_no_replan_when_all_false(self):
        assert should_replan() is False
