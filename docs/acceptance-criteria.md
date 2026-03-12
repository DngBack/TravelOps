# Acceptance criteria (AC)

## Functional

| ID | Criterion | How to verify |
|----|-----------|----------------|
| AC1 | Agent uses at least **3 tools** in happy path | Inspect trace: at least 3 tool spans (e.g. get_weather, search_hotels, estimate_transport or calculate_budget). |
| AC2 | At least **1 scenario** forces re-plan | Run severe-rain or hotel-empty scenario; trace should show planning/replan or changed strategy. |
| AC3 | At least **1 scenario** with tool timeout + retry + fallback | Run transport-timeout scenario; trace shows retry and fallback message or degraded result. |
| AC4 | Final answer includes **assumptions** and **warnings** | Final output JSON has `warnings` (and findings/assumptions where applicable). |

## Observability

| ID | Criterion | How to verify |
|----|-----------|----------------|
| AC5 | Each run produces **exactly 1 root trace** | Langfuse: one trace per `run_agent` invocation. |
| AC6 | Each **tool call** is a **separate child span** | Trace tree: one span per tool invocation. |
| AC7 | There is a **planning** span | Trace contains a planning (or equivalent) span. |
| AC8 | There is a **final_synthesis** span | Trace contains a final synthesis (or equivalent) span. |
| AC9 | Every **error** has **status + message + metadata** | Failed or fallback spans have error status and metadata (e.g. error_type). |
| AC10 | Traces can be **filtered by test_case_id** (and scenario_id) | In Langfuse, filter by metadata `test_case_id` / `scenario_id`. |

## Tester-demo

| ID | Criterion | How to verify |
|----|-----------|----------------|
| AC11 | At least **10 test scenarios** | See scenario matrix; tests in `tests/scenarios/` cover them. |
| AC12 | At least **3 failure scenarios** with **clear trace** showing cause | Run e.g. timeout, empty hotel, approval-required; trace shows why and how handled. |
| AC13 | **Dashboard** (or export) for **latency, failure rate, tool error rate** | Use Langfuse dashboards or export traces to compute metrics. |
