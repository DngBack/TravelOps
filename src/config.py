"""
TravelOps config: mode (instant / thinking), model names, logging.
"""
import os
from pathlib import Path


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
            or "gpt-5-mini"  # gpt-5-mini may be unavailable; override via env if needed
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


def get_log_file_absolute() -> Path | None:
    """
    Đường dẫn tuyệt đối tới file log (nếu đang bật ghi file).
    Đường dẫn tương đối được resolve theo thư mục làm việc hiện tại (giống FileHandler).
    """
    raw = get_log_file()
    if not raw:
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def log_file_uri(path: Path) -> str:
    """URI file:// để mở trong editor (Cursor/VS Code) hoặc dán vào terminal."""
    return path.as_uri()


def get_log_max_chars() -> int:
    """
    TRAVELOPS_LOG_MAX_CHARS: độ dài tối đa mỗi khối log (tool args, kết quả, LLM I/O).
    Mặc định 12000. Giới hạn 500–500000.
    """
    raw = (os.environ.get("TRAVELOPS_LOG_MAX_CHARS") or "12000").strip()
    try:
        n = int(raw)
    except ValueError:
        return 12000
    return max(500, min(n, 500_000))


def get_log_agent_io_verbose() -> bool:
    """TRAVELOPS_LOG_AGENT_IO_VERBOSE=1|true: ghi đầy đủ LLM input tại mức INFO (nặng)."""
    v = (os.environ.get("TRAVELOPS_LOG_AGENT_IO_VERBOSE") or "").strip().lower()
    return v in ("1", "true", "yes", "on")


def get_langfuse_detail_io() -> bool:
    """
    TRAVELOPS_LANGFUSE_DETAIL_IO: gửi input/output tool & LLM chi tiết lên Langfuse (observation type tool/span).
    Mặc định bật (1). Tắt: 0 | false.
    """
    v = (os.environ.get("TRAVELOPS_LANGFUSE_DETAIL_IO") or "1").strip().lower()
    return v not in ("0", "false", "no", "off")
