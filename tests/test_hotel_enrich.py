"""Hotel name extraction from web snippets."""
from src.tools.hotel_enrich import extract_hotel_names_from_text, merge_hotel_web_results
from src.tools.api_clients import deep_links_transport


def test_extracts_hotel_with_suffix():
    text = "1. HAIAN Beach Hotel · (4,330 reviews). Hadana Boutique Hotel nearby."
    names = extract_hotel_names_from_text(text)
    assert any("HAIAN" in n for n in names)
    assert any("Hadana" in n for n in names)


def test_merge_prefers_named_rows():
    raw = [
        {
            "title": "Khách sạn tại Đà Nẵng - Hotels.com",
            "link": "https://example.com/h",
            "snippet": "Royal Beachfront Resort Đà Nẵng · Wyndham Soleil Danang · M Hotel Danang",
        }
    ]
    merged = merge_hotel_web_results(raw)
    assert len(merged) >= 2
    names = {m["name"] for m in merged}
    assert any("Royal" in n or "Resort" in n for n in names)


def test_deep_links_has_flight_and_train():
    d = deep_links_transport("Hà Nội", "Đà Nẵng", "2025-06-01")
    assert d["flight"]
    assert d["train"]
    assert any("skyscanner" in u.lower() for u in d["flight"])
    assert any("dsvn" in u.lower() for u in d["train"])
