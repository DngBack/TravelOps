# TravelOps

TravelOps is an agent demo for tester training: plan → tools → re-plan → error handling → synthesis, with full trace observability on Langfuse.

## Quick start (dùng uv)

```bash
# 1. Cài uv: https://docs.astral.sh/uv/
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Tạo .venv và cài dependency
uv sync --all-extras

# 3. Cấu hình (bắt buộc: OPENAI_API_KEY)
cp .env.example .env
# Sửa .env, thêm OPENAI_API_KEY=sk-proj-...

# 4. Chạy agent
uv run python run_agent.py
# Hoặc prompt tùy ý:
uv run python run_agent.py "Lập kế hoạch Hà Nội → Đà Nẵng cuối tuần, thời tiết khách sạn ngân sách"
```

**Hướng dẫn từng bước:** [docs/run-with-uv.md](docs/run-with-uv.md)

## Streamlit UI (testing)

```bash
uv run streamlit run app.py
```

- Enter a prompt (default: Hanoi → Da Nang weekend trip).
- Choose a **scenario preset** to tag traces (e.g. "Severe rain", "Approval required") for filtering in Langfuse.
- Run agent and view the final answer; expand **Run steps** to see a trace-style preview of tool calls and outputs.

## Tools (7 tools — dùng API thật khi có cấu hình)

| Tool | API (ưu tiên) | API thay thế | Cấu hình |
|------|----------------|--------------|----------|
| **get_weather** | [Open-Meteo](https://open-meteo.com/) | — | Không cần key |
| **search_hotels** | [Amadeus](https://developers.amadeus.com/) Hotel List | [HotelsAPI.com](https://hotels-api.com/) search by city | `AMADEUS_*` hoặc `HOTELS_API_KEY` |
| **estimate_transport** | Amadeus Flight Offers (có giá) | [AviationStack](https://aviationstack.com/) routes (không giá) | `AMADEUS_*` hoặc `AVIATIONSTACK_ACCESS_KEY` |
| **calculate_budget** | Logic trong code | — | — |
| **risk_policy_advisor** | Logic từ weather/budget | — | — |
| **currency_fx** | [Frankfurter](https://www.frankfurter.app/) | — | Không cần key |
| **human_approval** | — | — | Luôn "pending" |
| **web_search** | [DuckDuckGo](https://pypi.org/project/duckduckgo-search/) | — | Không cần key (đã có trong dependencies) |

- **Web search:** Chỉ dùng DuckDuckGo (`duckduckgo-search`). Tra thông tin trực tiếp: khách sạn, giá vé, thời tiết. Cài: `pip install duckduckgo-search` hoặc `pip install -e .`.
- **Bật/tắt API thật:** `TRAVELOPS_USE_REAL_API=1` (mặc định) hoặc `=0` để chỉ stub.
- **Hotels:** Nếu có Amadeus key thì dùng Amadeus; không thì dùng HotelsAPI.com khi set `HOTELS_API_KEY` (đăng ký [hotels-api.com](https://hotels-api.com/register.php), 500 req/tháng free).
- **Flights:** Amadeus trả giá vé; AviationStack chỉ trả routes + duration (không giá), cần [aviationstack.com](https://aviationstack.com/) (routes có trên Basic plan trở lên).
- Chi tiết: `src/tools/api_clients.py`; wiring: `src/tools/core.py`.

## Structure

- **src/agents/** — TripOrchestrator, ResearchAgent, RiskAgent
- **src/tools/** — 7 tools (định nghĩa trong `core.py`, schema trong `schemas.py`, mock trong `mocks/`)
- **src/state/** — Workflow state machine and re-plan rules
- **src/output/** — Final answer contract (JSON + NL)
- **src/tracing/** — Langfuse + OpenInference instrumentation
- **tests/scenarios/** — Planning, tool orchestration, robustness, observability, safety, and 10 integration scenarios
- **docs/** — [Trace observability](docs/trace-observability.md), [Acceptance criteria](docs/acceptance-criteria.md), [Scenario matrix](docs/scenario-matrix.md)

## Tests

```bash
.venv/bin/pytest tests/ -m "not integration"   # unit tests
.venv/bin/pytest tests/ -v                      # all (integration skipped without OPENAI_API_KEY)
```

## Tester docs

See [docs/README.md](docs/README.md) for trace reading, AC checklist, and scenario matrix.
