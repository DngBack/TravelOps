"""
Trích tên khách sạn cụ thể từ kết quả web (snippet/title) thay vì chỉ trang tổng hợp.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

# Tiêu đề rõ ràng là trang danh mục — ưu tiên lấy tên từ snippet
_AGG_TITLE_PAT = re.compile(
    r"(khách\s*sạn\s*tại|hotels?\s+in|best\s+hotels|tất\s*cả\s*khách|all\s+hotels|"
    r"discount|tìm\s*kiếm|search|region/)",
    re.I,
)


def _norm_key(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s.lower().strip())


def _clean_fragment(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"^[\d\.\)\-\•·]+\s*", "", s)
    return s.strip(" ·•-|,")[:80]


def _is_plausible_hotel_name(name: str) -> bool:
    if len(name) < 6 or len(name) > 72:
        return False
    low = name.lower()
    if _AGG_TITLE_PAT.search(name) and "hotel" not in low and "resort" not in low:
        return False
    bad = (
        "discount tới",
        "best value",
        "places to stay",
        "highly recommend",
        "amenities for",
        "bedroom ",
        "exterior /",
        "nằm ở đà nẵng",
    )
    if any(b in low for b in bad):
        return False
    if low.count("http") or low.count("www."):
        return False
    return True


def extract_hotel_names_from_text(text: str, *, max_names: int = 24) -> list[str]:
    """Rút danh sách tên khách sạn có vẻ hợp lệ từ một đoạn văn bản."""
    if not text:
        return []
    seen: set[str] = set()
    out: list[str] = []

    patterns = [
        # "HAIAN Beach Hotel & Spa", "Grand Mercure Da Nang"
        re.compile(
            r"\b((?:[A-ZĐ][\w'\-]+(?:\s+[A-ZĐ][\w'\-]+){0,7})\s+"
            r"(?:Hotels?|Resorts?|Suites|Residence)(?:\s*&\s*Spa)?)\b",
            re.UNICODE,
        ),
        # "Khách sạn Mandila Beach Đà Nẵng"
        re.compile(
            r"Khách\s+sạn\s+([^\n·•]{3,55}?)(?=\s*[·,.;|]|\s*$|\n)",
            re.UNICODE | re.IGNORECASE,
        ),
        # TripAdvisor style: "1. HAIAN Beach Hotel ·"
        re.compile(
            r"(?:^|[\n;•·]|\d+\.\s+)\s*([A-ZĐ][^·•\n]{4,60}?(?:Hotel|Resort|Suites|Spa|Danang|Đà Nẵng))\s*·?",
            re.UNICODE | re.MULTILINE,
        ),
    ]
    for pat in patterns:
        for m in pat.finditer(text):
            frag = _clean_fragment(m.group(1))
            if not frag or not _is_plausible_hotel_name(frag):
                continue
            k = _norm_key(frag)
            if k in seen:
                continue
            seen.add(k)
            out.append(frag)
            if len(out) >= max_names:
                return out
    return out


def merge_hotel_web_results(raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    raw_rows: {title, link, snippet} từ Tavily.
    Trả về danh sách {name, link, snippet, source_title} — ưu tiên hàng có tên cụ thể.
    """
    structured: list[dict[str, Any]] = []
    for r in raw_rows:
        title = (r.get("title") or "").strip()
        link = (r.get("link") or "").strip()
        snippet = (r.get("snippet") or "").strip()
        blob = f"{title}\n{snippet}"
        names = extract_hotel_names_from_text(blob)
        title_is_agg = bool(_AGG_TITLE_PAT.search(title)) and len(names) > 0

        if names:
            for n in names[:4]:
                structured.append(
                    {
                        "name": n,
                        "link": link,
                        "snippet": snippet[:400],
                        "source_title": title,
                        "from_snippet": title_is_agg or n not in title,
                    }
                )
        else:
            # Giữ một dòng tổng hợp nếu không trích được tên (fallback)
            if title and link:
                structured.append(
                    {
                        "name": title[:120],
                        "link": link,
                        "snippet": snippet[:400],
                        "source_title": title,
                        "from_snippet": False,
                    }
                )

    # Dedupe theo tên khách sạn, giữ link đầu tiên
    by_name: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for row in structured:
        k = _norm_key(row["name"])
        if k not in by_name:
            by_name[k] = row
            order.append(k)
        elif row.get("from_snippet") and not by_name[k].get("from_snippet"):
            by_name[k] = row

    return [by_name[k] for k in order]
