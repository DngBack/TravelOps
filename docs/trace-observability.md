# Trace observability (for testers)

## Goal

TravelOps runs are traced so you can see the full story: plan, tool calls, re-plan (if any), errors, and final synthesis. Traces are sent to **Langfuse** when configured (OpenTelemetry/OpenInference). You do **not** see raw “hidden” chain-of-thought; you see **plan / decision summary / rationale** the app exposes.

## Trace tree shape

- **Root**: `workflow: travel_ops_agent`
- **Child spans** (typical order):
  - `input_validation` (if implemented)
  - `planning`
  - `tool:get_weather`, `tool:search_hotels`, `tool:estimate_transport`
  - (optional) `planning:replan` when re-plan triggers
  - `tool:calculate_budget`
  - `agent:risk_agent` (nested when sub-agents are used)
  - `final_synthesis`

Each span should have: **input**, **output**, **latency**, **token/cost** (for LLM), **error status**, **retry_count**, and **metadata** (e.g. scenario_id, test_case_id, tool_name, plan_step_id, fallback_used, severity).

## Root trace metadata

Filter and tag runs using:

| Field | Purpose |
|-------|---------|
| `app` | `travel_ops_agent` |
| `env` | staging / prod |
| `scenario_id` | e.g. SCN_004_TIMEOUT |
| `test_case_id` | e.g. TC_TOOL_017 |
| `user_role` | e.g. tester |
| `agent_version`, `prompt_version`, `toolset_version` | Versioning |

Set `SCENARIO_ID` and `TEST_CASE_ID` (env or in code) so you can filter traces in Langfuse by scenario/test case (AC10).

## Span metadata (per step)

- **status**: success / error / fallback / skipped  
- **latency_ms**, **retry_count**, **error_type**, **degraded_mode**  
- **tool_name**, **plan_step_id**, **fallback_used**, **severity**

## What “thinking” looks like

We do **not** log raw hidden CoT. We log:

- **plan_json** (or equivalent): structured plan the model produced  
- **decision_summary**: short text rationale  
- **Rationale for fallback / final recommendation**: why re-plan or final answer was chosen  

Use these to audit behavior without relying on raw reasoning content.

## How to run with tracing

1. Set Langfuse env vars (see `.env.example`): `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`.
2. Install: `openinference-instrumentation-openai-agents` is used to send OpenAI Agents spans to Langfuse.
3. Run the agent (e.g. `python run_agent.py "your prompt"`). Optionally set `SCENARIO_ID` and `TEST_CASE_ID`.
4. In Langfuse, open the trace for that run and check the tree and metadata above.
