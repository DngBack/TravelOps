"""
TravelOps Agent — Simple Streamlit UI for testing.
Run: streamlit run app.py
"""
import asyncio
import json
import os

from dotenv import load_dotenv

load_dotenv()


def _st_display_jsonish(label: str, data) -> None:
    """Streamlit st.json chỉ ổn với dict/list; scalar thì hiển thị an toàn."""
    if data is None:
        st.caption("_Trống._")
        return
    if isinstance(data, (dict, list)):
        st.json(data)
    elif isinstance(data, str):
        st.code(data, language="json")
    else:
        try:
            st.json(json.loads(json.dumps(data, default=str)))
        except (TypeError, ValueError):
            st.code(str(data), language=None)

from src.agent_io_serialize import (
    group_new_items_with_tool_io,
    run_item_public_dict,
    summarize_model_response,
    to_jsonable,
)
from src.config import get_log_file_absolute, log_file_uri
from src.logging_config import setup_logging

setup_logging()

import streamlit as st

# Default prompt for quick testing
DEFAULT_PROMPT = (
    "Lập kế hoạch chuyến đi Hà Nội → Đà Nẵng cuối tuần này, "
    "kiểm tra thời tiết, gợi ý khách sạn, tính ngân sách sơ bộ, "
    "và nếu có rủi ro mưa lớn thì đề xuất phương án dự phòng."
)

# Scenario presets for trace filtering (from docs/scenario-matrix.md)
SCENARIO_PRESETS = {
    "None": ("", ""),
    "Happy path": ("SCN_001_HAPPY", "TC_HAPPY_01"),
    "Severe rain": ("SCN_002_SEVERE_RAIN", "TC_RAIN_01"),
    "Hotel empty": ("SCN_003_HOTEL_EMPTY", "TC_HOTEL_01"),
    "Transport timeout": ("SCN_004_TIMEOUT", "TC_TIMEOUT_01"),
    "Conflicting prices": ("SCN_005_CONFLICT", "TC_CONFLICT_01"),
    "Missing constraint": ("SCN_006_MISSING_CONSTRAINT", "TC_MISSING_01"),
    "Approval required": ("SCN_007_APPROVAL", "TC_APPROVAL_01"),
    "Loop trap": ("SCN_008_LOOP_TRAP", "TC_LOOP_01"),
    "Hallucination trap": ("SCN_009_HALLUCINATION", "TC_HALL_01"),
    "Parallel race": ("SCN_010_PARALLEL_RACE", "TC_PARALLEL_01"),
}


def _run_agent(prompt: str, scenario_id: str, test_case_id: str):
    """Run agent and return (output_text, result_or_none)."""
    from run_agent import run_async

    return asyncio.run(
        run_async(
            prompt,
            scenario_id=scenario_id,
            test_case_id=test_case_id,
            return_result=True,
        )
    )


st.set_page_config(
    page_title="TravelOps Agent",
    page_icon="✈️",
    layout="centered",
)

st.title("✈️ TravelOps Agent")
st.caption("Plan → tools → re-plan → synthesize. Use scenario presets to tag traces in Langfuse.")

with st.form("run_form"):
    prompt = st.text_area(
        "User prompt",
        value=DEFAULT_PROMPT,
        height=120,
        help="Task for the agent (e.g. trip planning Hanoi → Da Nang).",
    )
    mode = st.selectbox(
        "Mode",
        options=["instant", "thinking"],
        index=0,
        help="instant = fast model (gpt-4o-mini). thinking = reasoning model (gpt-4.1-nano / gpt-5-nano).",
    )
    preset = st.selectbox(
        "Scenario preset (for trace filtering)",
        options=list(SCENARIO_PRESETS.keys()),
        help="Sets scenario_id / test_case_id on the trace.",
    )
    scenario_id, test_case_id = SCENARIO_PRESETS[preset]
    col1, col2 = st.columns(2)
    with col1:
        scenario_override = st.text_input("scenario_id (override)", value=scenario_id)
    with col2:
        test_case_override = st.text_input("test_case_id (override)", value=test_case_id)
    log_verbose = st.checkbox(
        "Ghi log LLM đầy đủ ra console/file (TRAVELOPS_LOG_AGENT_IO_VERBOSE)",
        value=False,
        help="Bật để mức INFO gồm llm_input_dump, llm_output_dump, system prompt và final_output đầy đủ.",
    )
    submitted = st.form_submit_button("Run agent")

if submitted:
    if not os.environ.get("OPENAI_API_KEY"):
        st.error("Set OPENAI_API_KEY in the environment to run the agent.")
        st.stop()

    os.environ["TRAVELOPS_MODE"] = mode
    if log_verbose:
        os.environ["TRAVELOPS_LOG_AGENT_IO_VERBOSE"] = "1"
    else:
        os.environ.pop("TRAVELOPS_LOG_AGENT_IO_VERBOSE", None)

    with st.spinner("Running agent (plan → tools → synthesis)…"):
        try:
            output_text, result = _run_agent(
                prompt,
                scenario_id=scenario_override,
                test_case_id=test_case_override,
            )
        except Exception as e:
            st.exception(e)
            st.stop()

    if result is None:
        st.warning("Agent not available. Install: pip install openai-agents")
        st.stop()

    st.success("Done")
    log_abs = get_log_file_absolute()
    if log_abs is not None:
        uri = log_file_uri(log_abs)
        st.markdown("**Log file (copy để mở trong editor / terminal)**")
        st.code(f"Path:\n{log_abs}\n\nfile URI:\n{uri}", language=None)
        st.caption(
            "Trình duyệt thường chặn mở file:// — copy Path hoặc dán URI vào Cursor: "
            "File → Open File from URL."
        )
    else:
        st.caption(
            "Không ghi file log (đặt `TRAVELOPS_LOG_FILE` rỗng để tắt). "
            "Mặc định: `logs/travelops.log`."
        )
    st.subheader("Final answer")
    st.markdown(output_text or "_No output._")

    if hasattr(result, "new_items") and result.new_items:
        with st.expander("Công cụ — input / output (gộp theo call_id)", expanded=True):
            st.caption(
                "Mỗi dòng = một lần gọi tool: **Input** (arguments) và **Output** (kết quả thực thi)."
            )
            blocks = group_new_items_with_tool_io(result.new_items)
            n_tool = 0
            for block in blocks:
                if block.get("display_kind") != "tool_input_output":
                    continue
                n_tool += 1
                name = block.get("tool_name") or "tool"
                cid = block.get("call_id") or "?"
                ag = block.get("agent_name") or ""
                st.markdown(f"**{n_tool}. `{name}`** · `{cid}`" + (f" · _{ag}_" if ag else ""))
                col_in, col_out = st.columns(2)
                with col_in:
                    st.markdown("**Input**")
                    inp = block.get("input")
                    if inp is not None:
                        _st_display_jsonish("input", inp)
                    elif block.get("input_arguments_raw"):
                        st.code(block["input_arguments_raw"], language="json")
                    else:
                        st.caption("_Không có arguments._")
                with col_out:
                    st.markdown("**Output**")
                    out = block.get("output")
                    if out is not None:
                        _st_display_jsonish("output", out)
                    else:
                        st.warning(
                            "Không có output ghép được — xem bước `tool_call_output_item` trong JSON thô bên dưới."
                        )
                st.divider()
            if n_tool == 0:
                st.info("Không có tool_call_item trong run này.")

        with st.expander("Run steps (tóm tắt)", expanded=False):
            for i, item in enumerate(result.new_items, 1):
                kind = getattr(item, "type", None) or type(item).__name__
                st.markdown(f"{i}. **{kind}**")

        with st.expander("Chi tiết I/O từng bước (JSON thô)", expanded=False):
            st.caption(
                "Mỗi phần tử trong `new_items`: gọi công cụ, kết quả công cụ, tin nhắn assistant, v.v."
            )
            for i, item in enumerate(result.new_items, 1):
                st.subheader(f"Bước {i}: {getattr(item, 'type', None) or type(item).__name__}")
                try:
                    st.json(run_item_public_dict(item))
                except Exception as e:
                    st.warning(f"Không serialize được: {e}")
                    st.text(str(item)[:4000])

    if getattr(result, "raw_responses", None):
        with st.expander("Phản hồi model từng lượt (raw_responses)", expanded=False):
            for ri, resp in enumerate(result.raw_responses, 1):
                st.subheader(f"Lượt model {ri}")
                try:
                    st.text(summarize_model_response(resp, max_chars=50_000))
                except Exception as e:
                    st.warning(str(e))
                    st.text(repr(resp)[:8000])

    with st.expander("Đầu vào run (input đã gửi cho Runner)", expanded=False):
        st.json(to_jsonable(getattr(result, "input", None)))

    if scenario_override or test_case_override:
        st.caption(f"Trace metadata: scenario_id={scenario_override or '-'}  test_case_id={test_case_override or '-'}")
