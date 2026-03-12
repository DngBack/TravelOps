"""
TravelOps Agent — Simple Streamlit UI for testing.
Run: streamlit run app.py
"""
import asyncio
import os

from dotenv import load_dotenv
load_dotenv()

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


def _format_step(item) -> str:
    """Format a run item for display (tool call, output, etc.)."""
    kind = type(item).__name__
    if hasattr(item, "name") and hasattr(item, "arguments"):
        return f"**{kind}**: `{getattr(item, 'name', '')}`"
    if hasattr(item, "output"):
        out = getattr(item, "output", "")
        if isinstance(out, str) and len(out) > 200:
            out = out[:200] + "..."
        return f"**{kind}**: {out}"
    return str(item)[:150]


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
    submitted = st.form_submit_button("Run agent")

if submitted:
    if not os.environ.get("OPENAI_API_KEY"):
        st.error("Set OPENAI_API_KEY in the environment to run the agent.")
        st.stop()

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
    st.subheader("Final answer")
    st.markdown(output_text or "_No output._")

    # Show run steps (tool calls / outputs) if available
    if hasattr(result, "new_items") and result.new_items:
        with st.expander("Run steps (trace preview)", expanded=False):
            for i, item in enumerate(result.new_items, 1):
                st.markdown(f"{i}. {_format_step(item)}")

    if scenario_override or test_case_override:
        st.caption(f"Trace metadata: scenario_id={scenario_override or '-'}  test_case_id={test_case_override or '-'}")
