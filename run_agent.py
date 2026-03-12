"""
TravelOps Agent entrypoint. Run with tracing (workflow: travel_ops_agent) and optional metadata.
"""
import asyncio
import os
import sys

from dotenv import load_dotenv
load_dotenv()

from src.tracing.langfuse_setup import setup_tracing, get_trace_metadata
from src.agents.orchestrator import create_orchestrator_agent


DEFAULT_INPUT = (
    "Lập kế hoạch chuyến đi Hà Nội → Đà Nẵng cuối tuần này, "
    "kiểm tra thời tiết, gợi ý khách sạn, tính ngân sách sơ bộ, "
    "và nếu có rủi ro mưa lớn thì đề xuất phương án dự phòng."
)


async def run_async(
    user_input: str,
    scenario_id: str = "",
    test_case_id: str = "",
    *,
    return_result: bool = False,
):
    """
    Run the TravelOps agent. Returns final_output str by default.
    If return_result=True, returns (final_output, result) for UI to show new_items/steps.
    """
    setup_tracing()

    try:
        from agents import Runner
    except ImportError:
        Runner = None
    try:
        from agents.tracing import trace
    except ImportError:
        try:
            from agents import trace
        except ImportError:
            trace = None
    try:
        from langfuse import get_client, propagate_attributes
    except ImportError:
        get_client = None
        propagate_attributes = None

    agent = create_orchestrator_agent(use_subagents=True)

    if Runner is None:
        if return_result:
            return "", None
        return "Install openai-agents to run the agent."

    metadata = get_trace_metadata(
        scenario_id=scenario_id or os.environ.get("SCENARIO_ID", ""),
        test_case_id=test_case_id or os.environ.get("TEST_CASE_ID", ""),
    )

    if trace is not None:
        with trace("workflow: travel_ops_agent"):
            if propagate_attributes is not None:
                with propagate_attributes(metadata=metadata):
                    result = await Runner.run(agent, user_input)
            else:
                result = await Runner.run(agent, user_input)
    else:
        result = await Runner.run(agent, user_input)

    try:
        langfuse = get_client()
        langfuse.flush()
    except Exception:
        pass

    if return_result:
        return result.final_output or "", result
    return result.final_output or ""


def main() -> None:
    user_input = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INPUT
    scenario_id = os.environ.get("SCENARIO_ID", "")
    test_case_id = os.environ.get("TEST_CASE_ID", "")
    output = asyncio.run(
        run_async(user_input, scenario_id=scenario_id, test_case_id=test_case_id)
    )
    print(output)


if __name__ == "__main__":
    main()
