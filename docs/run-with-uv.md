# Chạy TravelOps với uv

Dùng [uv](https://docs.astral.sh/uv/) để tạo môi trường ảo và cài dependency. Các bước dưới giả định bạn đang ở thư mục gốc của project (`TravelOps/`).

---

## Bước 1: Cài uv

**Linux/macOS (lệnh chung):**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Hoặc dùng pip (nếu đã có Python):**
```bash
pip install uv
```

**Kiểm tra:**
```bash
uv --version
```

---

## Bước 2: Tạo virtualenv và cài dependency

```bash
cd /path/to/TravelOps

# Tạo .venv và cài toàn bộ dependency từ pyproject.toml (bao gồm dev)
uv sync --all-extras
```

- `uv sync` đọc `pyproject.toml`, tạo/ dùng `.venv`, cài dependencies và ghi lock file `uv.lock`.
- `--all-extras` cài luôn optional groups (`dev`, `ui`).

**Chỉ cài dependency chính (không dev/ui):**
```bash
uv sync
```

**Cài thêm Streamlit (UI):**
```bash
uv sync --extra ui
```

---

## Bước 3: Cấu hình biến môi trường

Tạo file `.env` từ mẫu và sửa giá trị (ít nhất `OPENAI_API_KEY`):

```bash
cp .env.example .env
# Mở .env và điền OPENAI_API_KEY=sk-proj-... (bắt buộc để chạy agent)
```

Các biến quan trọng:

| Biến | Bắt buộc | Ghi chú |
|------|----------|--------|
| `OPENAI_API_KEY` | Có | Key OpenAI để agent chạy |
| `TRAVELOPS_USE_REAL_API` | Không | `1` (mặc định) hoặc `0` (chỉ stub) |
| `LANGFUSE_*` | Không | Nếu muốn trace lên Langfuse |
| `AMADEUS_*` / `HOTELS_API_KEY` / `AVIATIONSTACK_*` | Không | Cho hotel/flight API thật |

---

## Bước 4: Chạy agent (CLI)

Ứng dụng tự load `.env` (nhờ `python-dotenv`). Chạy từ thư mục gốc project:

```bash
uv run python run_agent.py
```

Với prompt tùy ý:
```bash
uv run python run_agent.py "Lập kế hoạch Hà Nội → Đà Nẵng cuối tuần, thời tiết khách sạn ngân sách"
```

**Chạy bằng .venv đã activate:**
```bash
source .venv/bin/activate   # Linux/macOS
# hoặc  .venv\Scripts\activate   trên Windows
python run_agent.py "Câu lệnh của bạn"
```
(.env vẫn được load tự động.)

---

## Bước 5: Chạy Streamlit UI

```bash
uv run streamlit run app.py
```

Hoặc sau khi `source .venv/bin/activate` và load `.env`:
```bash
streamlit run app.py
```

Mở URL in ra (thường `http://localhost:8501`), nhập prompt và chọn scenario nếu cần.

---

## Bước 6: Chạy test

**Unit test (không cần OPENAI_API_KEY):**
```bash
uv run pytest tests/ -m "not integration" -v
```

**Toàn bộ test (integration sẽ skip nếu không có OPENAI_API_KEY):**
```bash
uv run pytest tests/ -v
```

**Chạy với .env đã load (để integration test chạy khi có key):**
```bash
set -a && source .env && set +a
uv run pytest tests/ -v
```

---

## Tóm tắt lệnh thường dùng

| Mục đích | Lệnh |
|----------|------|
| Cài uv | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Tạo venv + cài deps | `uv sync --all-extras` |
| Chạy agent | `uv run python run_agent.py "prompt"` |
| Chạy Streamlit | `uv run streamlit run app.py` |
| Chạy test | `uv run pytest tests/ -m "not integration" -v` |
| Cập nhật lock file | `uv lock` |
| Thêm dependency mới | `uv add ten-package` |

---

## Ghi chú

- Ứng dụng dùng `python-dotenv` để load `.env` khi chạy `run_agent.py` hoặc `app.py`; không cần `source .env` thủ công.
- `uv run` dùng `.venv` của project. Chạy từ thư mục gốc TravelOps để đường dẫn `.env` đúng.
- Nếu muốn commit lock file để mọi người dùng cùng phiên bản dependency: giữ `uv.lock` và chạy `uv sync` (không cần `--all-extras` nếu không cần dev/ui).
