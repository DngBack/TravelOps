"""Serialize helpers for agent I/O logs / UI."""
import pytest

from src.agent_io_serialize import (
    dumps_compact,
    format_llm_input_items,
    group_new_items_with_tool_io,
    to_jsonable,
)


class _Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def test_to_jsonable_primitives():
    assert to_jsonable(None) is None
    assert to_jsonable({"a": 1}) == {"a": 1}
    assert to_jsonable([1, "x"]) == [1, "x"]


def test_dumps_compact_truncates():
    long = "x" * 100
    s = dumps_compact(long, max_chars=20)
    assert s.endswith("...")
    assert len(s) == 20


def test_format_llm_input_items_empty():
    assert format_llm_input_items([]) == "[]"
    assert format_llm_input_items(None) == "[]"


def test_group_new_items_pairs_tool_io():
    call = _Obj(
        type="tool_call_item",
        agent=_Obj(name="TripOrchestrator"),
        raw_item=_Obj(call_id="id1", name="search_hotels", arguments='{"destination":"DN"}'),
    )
    out = _Obj(
        type="tool_call_output_item",
        output={"hotels": [{"name": "H1"}]},
        raw_item={"call_id": "id1", "type": "function_call_output"},
    )
    blocks = group_new_items_with_tool_io([call, out])
    assert len(blocks) == 1
    assert blocks[0]["display_kind"] == "tool_input_output"
    assert blocks[0]["tool_name"] == "search_hotels"
    assert blocks[0]["input"] == {"destination": "DN"}
    assert blocks[0]["output"] == {"hotels": [{"name": "H1"}]}


def test_group_new_items_parallel_tools():
    c1 = _Obj(
        type="tool_call_item",
        agent=_Obj(name="A"),
        raw_item=_Obj(call_id="a", name="t1", arguments="{}"),
    )
    c2 = _Obj(
        type="tool_call_item",
        agent=_Obj(name="A"),
        raw_item=_Obj(call_id="b", name="t2", arguments="{}"),
    )
    o2 = _Obj(type="tool_call_output_item", output="2", raw_item={"call_id": "b"})
    o1 = _Obj(type="tool_call_output_item", output="1", raw_item={"call_id": "a"})
    blocks = group_new_items_with_tool_io([c1, c2, o2, o1])
    assert len(blocks) == 2
    assert blocks[0]["call_id"] == "a"
    assert blocks[0]["output"] == "1"
    assert blocks[1]["call_id"] == "b"
    assert blocks[1]["output"] == "2"
