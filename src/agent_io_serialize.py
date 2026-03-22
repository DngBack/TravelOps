"""
Chuyển input/output của agent (RunItem, LLM messages, ModelResponse) sang JSON-friendly
để ghi log và hiển thị trong Streamlit — không phụ thuộc vào TravelOpsRunHooks.
"""
from __future__ import annotations

import json
from typing import Any


def to_jsonable(obj: Any, depth: int = 0, max_depth: int = 24) -> Any:
    """Đệ quy an toàn: dict/list/scalar, Pydantic model_dump, còn lại -> str."""
    if depth > max_depth:
        return "<max_depth>"
    if obj is None or isinstance(obj, (bool, int, float)):
        return obj
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            out[str(k)] = to_jsonable(v, depth + 1, max_depth)
        return out
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(x, depth + 1, max_depth) for x in obj]
    model_dump = getattr(obj, "model_dump", None)
    if callable(model_dump):
        try:
            return to_jsonable(model_dump(mode="json", exclude_unset=True), depth + 1, max_depth)
        except TypeError:
            try:
                return to_jsonable(model_dump(exclude_unset=True), depth + 1, max_depth)
            except Exception:
                pass
    return str(obj)


def dumps_compact(obj: Any, *, max_chars: int = 8000, indent: int = 2) -> str:
    """JSON indent, cắt theo max_chars (dùng cho log)."""
    try:
        payload = to_jsonable(obj)
        s = json.dumps(payload, ensure_ascii=False, indent=indent)
    except (TypeError, ValueError):
        s = repr(obj)
    if max_chars > 0 and len(s) > max_chars:
        return s[: max_chars - 3] + "..."
    return s


def summarize_model_response(response: Any, *, max_chars: int = 12000) -> str:
    """Rút gọn ModelResponse: từng phần output (text / tool calls)."""
    parts: list[dict[str, Any]] = []
    output = getattr(response, "output", None) or []
    for i, item in enumerate(output):
        entry: dict[str, Any] = {"index": i, "type": type(item).__name__}
        name = getattr(item, "type", None)
        if name is not None:
            entry["item_type"] = str(name)
        # Assistant message text
        content = getattr(item, "content", None)
        if content is not None:
            texts: list[str] = []
            for block in content:
                t = getattr(block, "text", None)
                if isinstance(t, str):
                    texts.append(t)
                ref = getattr(block, "refusal", None)
                if isinstance(ref, str):
                    texts.append(f"[refusal] {ref}")
            if texts:
                entry["text"] = "\n".join(texts)
        # Function tool call
        if hasattr(item, "name") and hasattr(item, "arguments"):
            entry["tool_name"] = getattr(item, "name", "")
            entry["arguments"] = getattr(item, "arguments", "")
        parts.append(entry)
    usage = getattr(response, "usage", None)
    meta = {
        "response_id": getattr(response, "response_id", None),
        "request_id": getattr(response, "request_id", None),
        "usage": to_jsonable(usage) if usage is not None else None,
        "output": parts,
    }
    return dumps_compact(meta, max_chars=max_chars)


def run_item_public_dict(item: Any) -> dict[str, Any]:
    """Một RunItem thành dict (bỏ tham chiếu agent phức tạp)."""
    agent = getattr(item, "agent", None)
    agent_name = getattr(agent, "name", None) if agent is not None else None
    kind = getattr(item, "type", None) or type(item).__name__
    out: dict[str, Any] = {
        "run_item_type": kind,
        "agent_name": agent_name,
    }
    raw = getattr(item, "raw_item", None)
    if raw is not None:
        out["raw_item"] = to_jsonable(raw)
    if kind == "tool_call_output_item" or getattr(item, "type", None) == "tool_call_output_item":
        if hasattr(item, "output"):
            out["parsed_tool_output"] = to_jsonable(getattr(item, "output"))
    for opt in ("description", "title"):
        if hasattr(item, opt):
            v = getattr(item, opt, None)
            if v is not None:
                out[opt] = v
    return out


def format_llm_input_items(input_items: list[Any] | None, *, max_chars: int = 8000) -> str:
    if not input_items:
        return "[]"
    serialized = [to_jsonable(x) for x in input_items]
    return dumps_compact(serialized, max_chars=max_chars)


def _raw_tool_call_id(raw: Any) -> str | None:
    if raw is None:
        return None
    cid = getattr(raw, "call_id", None)
    if cid is not None:
        return str(cid)
    if isinstance(raw, dict):
        v = raw.get("call_id")
        return str(v) if v is not None else None
    return None


def _raw_tool_name(raw: Any) -> str | None:
    if raw is None:
        return None
    n = getattr(raw, "name", None)
    if n is not None:
        return str(n)
    if isinstance(raw, dict):
        v = raw.get("name")
        return str(v) if v is not None else None
    return None


def _raw_tool_arguments_str(raw: Any) -> str | None:
    if raw is None:
        return None
    a = getattr(raw, "arguments", None)
    if a is not None:
        return a if isinstance(a, str) else str(a)
    if isinstance(raw, dict):
        v = raw.get("arguments")
        if v is None:
            return None
        return v if isinstance(v, str) else str(v)
    return None


def parse_tool_call_arguments_json(arguments_str: str | None) -> Any:
    """Chuỗi JSON từ model → object; nếu lỗi parse thì trả về chuỗi gốc."""
    if not arguments_str or not str(arguments_str).strip():
        return None
    try:
        return json.loads(arguments_str)
    except json.JSONDecodeError:
        return arguments_str


def tool_call_input_summary(item: Any) -> dict[str, Any]:
    """Chỉ từ tool_call_item: tên tool, call_id, input đã parse."""
    raw = getattr(item, "raw_item", None)
    args_s = _raw_tool_arguments_str(raw)
    return {
        "tool_name": _raw_tool_name(raw),
        "call_id": _raw_tool_call_id(raw),
        "arguments_json": parse_tool_call_arguments_json(args_s),
        "arguments_raw": args_s,
    }


def normalize_tool_result_for_display(output: Any) -> Any:
    """Kết quả tool (object hoặc chuỗi JSON) → hiển thị JSON-friendly."""
    if output is None:
        return None
    if isinstance(output, str):
        s = output.strip()
        if s.startswith("{") or s.startswith("["):
            try:
                return json.loads(s)
            except json.JSONDecodeError:
                pass
        return output
    return to_jsonable(output)


def group_new_items_with_tool_io(items: list[Any] | None) -> list[dict[str, Any]]:
    """
    Gộp tool_call_item với tool_call_output_item (cùng call_id) thành một bản ghi
    có input + output. Dùng map theo call_id để đúng cả khi nhiều tool chạy song song.
    """
    if not items:
        return []
    outputs_by_id: dict[str, Any] = {}
    for it in items:
        k = getattr(it, "type", None) or type(it).__name__
        if k != "tool_call_output_item":
            continue
        cid = _raw_tool_call_id(getattr(it, "raw_item", None))
        if cid:
            outputs_by_id[cid] = it

    paired_output_ids: set[str] = set()
    out: list[dict[str, Any]] = []
    for item in items:
        kind = getattr(item, "type", None) or type(item).__name__
        if kind == "tool_call_output_item":
            cid = _raw_tool_call_id(getattr(item, "raw_item", None))
            if cid and cid in paired_output_ids:
                continue
            out.append(
                {
                    "display_kind": "orphan_tool_output",
                    "call_id": cid,
                    "detail": run_item_public_dict(item),
                }
            )
            continue
        if kind == "tool_call_item":
            summary = tool_call_input_summary(item)
            call_id = summary.get("call_id")
            agent = getattr(item, "agent", None)
            agent_name = getattr(agent, "name", None) if agent is not None else None
            merged: dict[str, Any] = {
                "display_kind": "tool_input_output",
                "agent_name": agent_name,
                "tool_name": summary.get("tool_name"),
                "call_id": call_id,
                "input": summary.get("arguments_json"),
                "input_arguments_raw": summary.get("arguments_raw"),
            }
            if call_id and call_id in outputs_by_id:
                nxt = outputs_by_id[call_id]
                parsed = getattr(nxt, "output", None)
                merged["output"] = normalize_tool_result_for_display(parsed)
                merged["output_raw_item"] = to_jsonable(getattr(nxt, "raw_item", None))
                paired_output_ids.add(call_id)
            else:
                merged["output"] = None
                if not call_id:
                    merged["note"] = "missing call_id; could not pair output"
            out.append(merged)
        else:
            out.append(
                {
                    "display_kind": "run_item",
                    "run_item_type": kind,
                    "detail": run_item_public_dict(item),
                }
            )
    return out
