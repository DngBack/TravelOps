"""
TravelOps logging: log mọi thông tin (input, tool calls, LLM, output).
Cấu hình qua TRAVELOPS_LOG_LEVEL, TRAVELOPS_LOG_FILE.
"""
import logging
from contextvars import ContextVar
from pathlib import Path

from src.agent_io_serialize import (
    format_llm_input_items,
    summarize_model_response,
)
from src.config import get_log_agent_io_verbose, get_log_file, get_log_level, get_log_max_chars

# Stack LLM (push start → pop end) để khớp khi lồng / song song trong cùng task
_travelops_llm_stack: ContextVar[list | None] = ContextVar("travelops_llm_stack", default=None)


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


def _truncate(s: str, max_len: int | None = None) -> str:
    if max_len is None:
        max_len = get_log_max_chars()
    if not s or len(s) <= max_len:
        return s or ""
    return s[:max_len] + "..."


def _tool_args_from_context(context) -> str:
    """OpenAI Agents SDK: ToolContext có tool_arguments (JSON string)."""
    raw = getattr(context, "tool_arguments", None)
    if isinstance(raw, str) and raw.strip():
        return raw
    tin = getattr(context, "tool_input", None)
    if tin is not None:
        return _truncate(str(tin))
    return ""


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
        instr = getattr(agent, "instructions", None)
        if isinstance(instr, str) and instr.strip():
            self._log.debug(
                "agent_instructions_preview | agent=%s | %s",
                name,
                _truncate(instr, min(2000, get_log_max_chars())),
            )

    async def on_agent_end(self, context, agent, output) -> None:
        name = getattr(agent, "name", str(agent))
        out_preview = _truncate(str(output) if output else "")
        self._log.info("agent_end | agent=%s | output_preview=%s", name, out_preview)
        if hasattr(context, "usage") and context.usage:
            self._log.debug("usage=%s", context.usage)
        try:
            from src.tracing.langfuse_detail import emit_agent_output_to_langfuse

            emit_agent_output_to_langfuse(agent_name=name, output_text=str(output) if output else "")
        except Exception:
            pass

    async def on_tool_start(self, context, agent, tool) -> None:
        name = getattr(tool, "name", str(tool))
        args = _truncate(_tool_args_from_context(context))
        call_id = getattr(context, "tool_call_id", "") or ""
        self._log.info(
            "tool_start | tool=%s | call_id=%s | args=%s",
            name,
            call_id or "-",
            args or "{}",
        )

    async def on_tool_end(self, context, agent, tool, result) -> None:
        name = getattr(tool, "name", str(tool))
        call_id = getattr(context, "tool_call_id", "") or ""
        body = str(result) if result is not None else ""
        self._log.info(
            "tool_end | tool=%s | call_id=%s | result=%s",
            name,
            call_id or "-",
            _truncate(body),
        )
        try:
            from src.tracing.langfuse_detail import emit_tool_to_langfuse

            ag = getattr(agent, "name", "") if agent is not None else ""
            args = _tool_args_from_context(context)
            emit_tool_to_langfuse(
                tool_name=name,
                call_id=call_id,
                arguments=args or "",
                result=body,
                agent_name=ag,
            )
        except Exception:
            pass

    async def on_llm_start(self, context, agent, system_prompt, input_items) -> None:
        agent_name = getattr(agent, "name", str(agent))
        num_items = len(input_items) if input_items else 0
        max_c = get_log_max_chars()
        stack = list(_travelops_llm_stack.get() or [])
        stack.append(
            {
                "agent_name": agent_name,
                "system_prompt": system_prompt,
                "input_items": input_items,
            }
        )
        _travelops_llm_stack.set(stack)
        self._log.info("llm_start | agent=%s | input_items=%s", agent_name, num_items)
        if system_prompt:
            sp = _truncate(system_prompt, max_c)
            if get_log_agent_io_verbose():
                self._log.info("llm_system_prompt | agent=%s | %s", agent_name, sp)
            else:
                self._log.debug("llm_system_prompt | agent=%s | %s", agent_name, sp)
        payload = format_llm_input_items(input_items, max_chars=max_c)
        if get_log_agent_io_verbose():
            self._log.info("llm_input_dump | agent=%s | %s", agent_name, payload)
        else:
            self._log.debug("llm_input_dump | agent=%s | %s", agent_name, payload)

    async def on_llm_end(self, context, agent, response) -> None:
        agent_name = getattr(agent, "name", str(agent))
        max_c = get_log_max_chars()
        summary = summarize_model_response(response, max_chars=max_c)
        if get_log_agent_io_verbose():
            self._log.info("llm_output_dump | agent=%s | %s", agent_name, summary)
        else:
            self._log.debug("llm_output_dump | agent=%s | %s", agent_name, summary)
        # Một dòng ngắn luôn có ở INFO
        n_blocks = len(getattr(response, "output", None) or [])
        self._log.info(
            "llm_end | agent=%s | output_blocks=%s",
            agent_name,
            n_blocks,
        )
        stack = list(_travelops_llm_stack.get() or [])
        pending = stack.pop() if stack else None
        _travelops_llm_stack.set(stack)
        try:
            from src.tracing.langfuse_detail import emit_llm_to_langfuse

            if pending:
                payload = format_llm_input_items(
                    pending.get("input_items"), max_chars=max_c
                )
                emit_llm_to_langfuse(
                    agent_name=pending.get("agent_name") or agent_name,
                    system_prompt=pending.get("system_prompt"),
                    input_items_dump=payload,
                    response_summary=summary,
                    output_block_count=n_blocks,
                )
            else:
                emit_llm_to_langfuse(
                    agent_name=agent_name,
                    system_prompt=None,
                    input_items_dump="",
                    response_summary=summary,
                    output_block_count=n_blocks,
                )
        except Exception:
            pass
