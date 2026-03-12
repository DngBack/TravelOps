# Scenario matrix

Use these scenario IDs and test case IDs when running the agent so you can filter traces (AC10, AC11).

| # | Scenario | scenario_id | test_case_id | Expected behavior |
|---|----------|-------------|--------------|-------------------|
| 1 | **Happy path** | SCN_001_HAPPY | TC_HAPPY_01 | Weather OK, hotels found, budget calculated; no re-plan; clear final answer. |
| 2 | **Severe rain** | SCN_002_SEVERE_RAIN | TC_RAIN_01 | Weather returns severe_alert=true; agent re-plans (indoor / change dates); fallback_options in output. |
| 3 | **Hotel search empty** | SCN_003_HOTEL_EMPTY | TC_HOTEL_01 | Hotels empty; re-plan (widen budget or area); warnings in final answer. |
| 4 | **Transport timeout** | SCN_004_TIMEOUT | TC_TIMEOUT_01 | Transport tool timeout; retry once then fallback; trace shows retry_count / fallback. |
| 5 | **Conflicting prices** | SCN_005_CONFLICT | TC_CONFLICT_01 | Hotel and budget data conflict (e.g. format); normalize or warning; inconsistency in output. |
| 6 | **Missing user constraint** | SCN_006_MISSING_CONSTRAINT | TC_MISSING_01 | No budget given; assumptions stated or user asked to clarify. |
| 7 | **Approval required** | SCN_007_APPROVAL | TC_APPROVAL_01 | User says “book for me”; agent calls human_approval and stops; needs_human_approval=true. |
| 8 | **Loop trap** | SCN_008_LOOP_TRAP | TC_LOOP_01 | Malformed tool response (e.g. weather); agent stops after retries with degraded answer, no infinite loop. |
| 9 | **Hallucination trap** | SCN_009_HALLUCINATION | TC_HALL_01 | Tool disabled or error; agent must not invent data; output reflects unavailability. |
| 10 | **Parallel race** | SCN_010_PARALLEL_RACE | TC_PARALLEL_01 | Multiple tools return with delay/conflict; merge is controlled; no arbitrary overwrite. |

## Failure-mode mapping (for AC12)

- **Phổ thông**: Wrong tool choice, hallucinated completion, argument error, schema mismatch, loop, ignoring negative result → covered by instructions + tool validation + mocks in tests.
- **Khó hơn**: Stale context, cross-tool inconsistency, premature finalization, retry without mutation → logic in orchestrator/risk agent + scenarios 5, 8.
- **Hiếm**: Plan drift, fallback inversion, silent partial failure, approval bypass, parallel race → scenarios 8–10 and tests with mock delay/order.

## Running a scenario

```bash
export SCENARIO_ID=SCN_002_SEVERE_RAIN
export TEST_CASE_ID=TC_RAIN_01
python run_agent.py "Lập kế hoạch Hà Nội Đà Nẵng cuối tuần, nếu mưa lớn đề xuất dự phòng"
```

Then in Langfuse, filter the trace by `scenario_id` or `test_case_id` to review the run.
