"""
TravelOps config: mode (instant / thinking), model names, logging.
"""
import os


def get_mode() -> str:
    """
    TRAVELOPS_MODE: instant (fast) | thinking (auto gpt-5-nano / reasoning).
    Default: instant.
    """
    v = (os.environ.get("TRAVELOPS_MODE") or "instant").strip().lower()
    return v if v in ("instant", "thinking") else "instant"


def get_model_for_mode(mode: str | None = None) -> str:
    """
    Model name for current mode. Override via TRAVELOPS_MODEL_INSTANT / TRAVELOPS_MODEL_THINKING.
    - instant: fast, default gpt-4o-mini
    - thinking: reasoning, default gpt-4.1-nano (or gpt-5-nano when available)
    """
    mode = mode or get_mode()
    if mode == "thinking":
        return (
            os.environ.get("TRAVELOPS_MODEL_THINKING", "").strip()
            or "gpt-5-nano"
        )
    return (
        os.environ.get("TRAVELOPS_MODEL_INSTANT", "").strip()
        or "gpt-4o-mini"
    )


def get_log_level() -> str:
    """TRAVELOPS_LOG_LEVEL: DEBUG | INFO | WARNING | ERROR. Default: INFO."""
    v = (os.environ.get("TRAVELOPS_LOG_LEVEL") or "INFO").strip().upper()
    return v if v in ("DEBUG", "INFO", "WARNING", "ERROR") else "INFO"


def get_log_file() -> str | None:
    """TRAVELOPS_LOG_FILE: path to log file. Default: logs/travelops.log (if set). Empty = no file."""
    return os.environ.get("TRAVELOPS_LOG_FILE", "logs/travelops.log").strip() or None
