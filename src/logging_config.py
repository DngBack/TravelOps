"""
TravelOps logging: log mọi thông tin (input, tool calls, LLM, output).
Cấu hình qua TRAVELOPS_LOG_LEVEL, TRAVELOPS_LOG_FILE.
"""
import logging
from pathlib import Path

from src.config import get_log_file, get_log_level


def setup_logging() -> logging.Logger:
    """
    Cấu hình logger "travelops": file (nếu có) + stdout, format có timestamp.
    Trả về logger để dùng trong RunHooks.
    """
    log_level = get_log_level()
    log_file = get_log_file()

    logger = logging.getLogger("travelops")
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    logger.handlers.clear()

    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt=date_fmt)

    sh = logging.StreamHandler()
    sh.setLevel(logger.level)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    if log_file:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(path, encoding="utf-8")
        fh.setLevel(logger.level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


def get_logger() -> logging.Logger:
    """Lấy logger travelops (gọi setup_logging trước nếu chưa)."""
    return logging.getLogger("travelops")


def _truncate(s: str, max_len: int = 500) -> str:
    if not s or len(s) <= max_len:
        return s or ""
    return s[:max_len] + "..."


def _get_run_hooks_class():
    try:
        from agents.lifecycle import RunHooks as BaseRunHooks
        return BaseRunHooks
    except ImportError:
        return object


class TravelOpsRunHooks(_get_run_hooks_class()):
    """
    RunHooks: log toàn bộ — agent start/end, tool start/end, LLM start/end.
    Gắn vào Runner.run(..., hooks=TravelOpsRunHooks()).
    """

    def __init__(self):
        super().__init__()
        self._log = get_logger()

    async def on_agent_start(self, context, agent) -> None:
        name = getattr(agent, "name", str(agent))
        self._log.info("agent_start | agent=%s", name)

    async def on_agent_end(self, context, agent, output) -> None:
        name = getattr(agent, "name", str(agent))
        out_preview = _truncate(str(output) if output else "")
        self._log.info("agent_end | agent=%s | output_preview=%s", name, out_preview)
        if hasattr(context, "usage") and context.usage:
            self._log.debug("usage=%s", context.usage)

    async def on_tool_start(self, context, agent, tool) -> None:
        name = getattr(tool, "name", str(tool))
        args = ""
        if hasattr(context, "tool_input"):
            args = _truncate(str(context.tool_input))
        elif getattr(context, "tool_input", None):
            args = _truncate(str(context.tool_input))
        self._log.info("tool_start | tool=%s | args=%s", name, args)

    async def on_tool_end(self, context, agent, tool, result) -> None:
        name = getattr(tool, "name", str(tool))
        self._log.info("tool_end | tool=%s | result_preview=%s", name, _truncate(str(result) if result else ""))

    async def on_llm_start(self, context, agent, system_prompt, input_items) -> None:
        agent_name = getattr(agent, "name", str(agent))
        num_items = len(input_items) if input_items else 0
        self._log.info("llm_start | agent=%s | input_items=%s", agent_name, num_items)
        if system_prompt:
            self._log.debug("system_prompt_preview=%s", _truncate(system_prompt, 300))

    async def on_llm_end(self, context, agent, response) -> None:
        agent_name = getattr(agent, "name", str(agent))
        out_preview = _truncate(str(getattr(response, "output", response)))
        self._log.info("llm_end | agent=%s | response_preview=%s", agent_name, out_preview)
