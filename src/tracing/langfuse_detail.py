"""
Gửi I/O chi tiết (tool, LLM) lên Langfuse — tương đương nội dung log travelops.
Dùng observation `travelops.tool.*` và `travelops.llm.*` để dễ lọc trong UI.
"""
from __future__ import annotations

from typing import Any

from src.config import get_langfuse_detail_io, get_log_max_chars


def _truncate(s: str, max_len: int | None = None) -> str:
    if max_len is None:
        max_len = get_log_max_chars()
    if not s or len(s) <= max_len:
        return s or ""
    return s[:max_len] + "..."


def _client_ok() -> Any | None:
    try:
        from langfuse import get_client

        lf = get_client()
        if getattr(lf, "tracing_enabled", True) is False:
            return None
        return lf
    except Exception:
        return None


def emit_tool_to_langfuse(
    *,
    tool_name: str,
    call_id: str,
    arguments: str,
    result: str,
    agent_name: str,
) -> None:
    if not get_langfuse_detail_io():
        return
    lf = _client_ok()
    if lf is None:
        return
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in (tool_name or "tool"))[:80]
    try:
        with lf.start_as_current_observation(
            name=f"travelops.tool.{safe_name}",
            as_type="tool",
            input={
                "call_id": call_id or None,
                "arguments": _truncate(arguments or ""),
            },
            output={"result": _truncate(result or "")},
            metadata={
                "source": "travelops_run_hooks",
                "agent": agent_name,
                "tool": tool_name,
            },
        ):
            pass
    except Exception:
        pass


def emit_llm_to_langfuse(
    *,
    agent_name: str,
    system_prompt: str | None,
    input_items_dump: str,
    response_summary: str,
    output_block_count: int,
) -> None:
    if not get_langfuse_detail_io():
        return
    lf = _client_ok()
    if lf is None:
        return
    safe_agent = "".join(c if c.isalnum() or c in "._-" else "_" for c in (agent_name or "agent"))[:80]
    inp: dict[str, Any] = {
        "input_items": _truncate(input_items_dump or ""),
        "input_items_chars": len(input_items_dump or ""),
    }
    if system_prompt:
        inp["system_prompt"] = _truncate(system_prompt)
    try:
        with lf.start_as_current_observation(
            name=f"travelops.llm.{safe_agent}",
            as_type="span",
            input=inp,
            output={
                "model_response_summary": _truncate(response_summary or ""),
                "output_blocks": output_block_count,
            },
            metadata={"source": "travelops_run_hooks", "agent": agent_name},
        ):
            pass
    except Exception:
        pass


def emit_agent_output_to_langfuse(*, agent_name: str, output_text: str) -> None:
    """Tùy chọn: kết quả cuối của agent (markdown)."""
    if not get_langfuse_detail_io():
        return
    lf = _client_ok()
    if lf is None:
        return
    safe_agent = "".join(c if c.isalnum() or c in "._-" else "_" for c in (agent_name or "agent"))[:80]
    try:
        with lf.start_as_current_observation(
            name=f"travelops.agent_end.{safe_agent}",
            as_type="span",
            input=None,
            output={"final_output": _truncate(output_text or "")},
            metadata={"source": "travelops_run_hooks", "agent": agent_name},
        ):
            pass
    except Exception:
        pass
