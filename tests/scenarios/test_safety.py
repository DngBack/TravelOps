"""
Group E — Safety / control: approval gate, no fabricated actions.
"""
import pytest
import json

from src.tools.core import _human_approval_impl
from src.output.contract import FinalAnswer


class TestApprovalGate:
    """AC: approval gate works; agent should stop for booking/email."""

    def test_human_approval_returns_pending(self):
        out = _human_approval_impl(action="book_hotel", payload="Hotel A, 2 nights")
        data = json.loads(out)
        assert data.get("status") == "pending"

    def test_final_answer_needs_human_approval_flag(self):
        a = FinalAnswer(needs_human_approval=True)
        assert a.to_json_dict()["needs_human_approval"] is True
