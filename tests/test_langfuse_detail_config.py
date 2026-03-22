"""Langfuse detail I/O flag."""
from src.config import get_langfuse_detail_io


def test_langfuse_detail_default_on(monkeypatch):
    monkeypatch.delenv("TRAVELOPS_LANGFUSE_DETAIL_IO", raising=False)
    assert get_langfuse_detail_io() is True


def test_langfuse_detail_off(monkeypatch):
    monkeypatch.setenv("TRAVELOPS_LANGFUSE_DETAIL_IO", "0")
    assert get_langfuse_detail_io() is False
