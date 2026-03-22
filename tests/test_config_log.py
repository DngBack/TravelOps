"""Log path resolution."""
from pathlib import Path

import pytest

from src import config


def test_get_log_file_absolute_resolves_relative(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TRAVELOPS_LOG_FILE", "logs/x.log")
    p = config.get_log_file_absolute()
    assert p is not None
    assert p == (tmp_path / "logs" / "x.log").resolve()


def test_log_file_uri_is_file_scheme(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TRAVELOPS_LOG_FILE", "a.log")
    p = config.get_log_file_absolute()
    assert p is not None
    uri = config.log_file_uri(p)
    assert uri.startswith("file://")


def test_get_log_file_absolute_none_when_disabled(monkeypatch):
    monkeypatch.setenv("TRAVELOPS_LOG_FILE", "")
    assert config.get_log_file() is None
    assert config.get_log_file_absolute() is None
