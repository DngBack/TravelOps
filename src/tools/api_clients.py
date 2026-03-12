"""
Real API clients for TravelOps tools.
- Open-Meteo: weather (no key)
- Frankfurter: exchange rates (no key)
- Amadeus: flights + hotels (AMADEUS_CLIENT_ID, AMADEUS_CLIENT_SECRET)
- HotelsAPI.com: hotels by city (HOTELS_API_KEY) — alternative to Amadeus
- AviationStack: flight routes (AVIATIONSTACK_ACCESS_KEY) — no prices
- DuckDuckGo: web search (duckduckgo-search, no key)
"""
import os
import re
from datetime import datetime
from typing import Any

import requests

from src.tools.schemas import (
    CurrencyFxOutput,
    GetWeatherOutput,
    HotelItem,
    SearchHotelsOutput,
    TransportOption,
    EstimateTransportOutput,
)

# Timeout for all HTTP calls
REQUEST_TIMEOUT = 15

# Vietnam city name -> IATA code (for Amadeus)
CITY_TO_IATA: dict[str, str] = {
    "hanoi": "HAN",
    "ha noi": "HAN",
    "hà nội": "HAN",
    "danang": "DAD",
    "da nang": "DAD",
    "đà nẵng": "DAD",
    "ho chi minh": "SGN",
    "ho chi minh city": "SGN",
    "sài gòn": "SGN",
    "saigon": "SGN",
    "hue": "HUI",
    "huế": "HUI",
    "nha trang": "CXR",
}


def _norm_city(s: str) -> str:
    return (s or "").strip().lower()


def _extract_first_date(dates: str) -> str | None:
    """Try to get YYYY-MM-DD from free-text dates."""
    if not dates:
        return None
    # ISO date
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", dates)
    if m:
        return m.group(0)
    # Try "dd/mm/yyyy" or "dd-mm-yyyy"
    m = re.search(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})", dates)
    if m:
        d, mo, y = m.group(1), m.group(2), m.group(3)
        return f"{y}-{mo.zfill(2)}-{d.zfill(2)}"
    return None


# --- Open-Meteo (weather) ---
def open_meteo_forecast(destination: str, dates: str) -> GetWeatherOutput | None:
    """Fetch weather from Open-Meteo. No API key. Returns None on error."""
    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": destination.strip(), "count": 1},
            timeout=REQUEST_TIMEOUT,
        )
        geo.raise_for_status()
        data = geo.json()
        results = data.get("results") or []
        if not results:
            return None
        lat = results[0]["latitude"]
        lon = results[0]["longitude"]
        tz = results[0].get("timezone", "Asia/Bangkok")

        forecast = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "timezone": tz,
                "daily": "weathercode,precipitation_probability_max,temperature_2m_max,temperature_2m_min",
            },
            timeout=REQUEST_TIMEOUT,
        )
        forecast.raise_for_status()
        daily = forecast.json().get("daily") or {}
        codes = daily.get("weathercode") or [0]
        precip = daily.get("precipitation_probability_max") or [0]
        tmax = daily.get("temperature_2m_max") or [0]
        tmin = daily.get("temperature_2m_min") or [0]

        # First day
        code = int(codes[0]) if codes else 0
        rain_p = float(precip[0]) / 100.0 if precip else 0.0
        tm = (float(tmax[0]) + float(tmin[0])) / 2 if (tmax and tmin) else 0.0

        # WMO codes: 95,96,99 = thunderstorm; 71-77 snow; 80-82,56,57,66,67 = heavy precip
        severe_codes = {95, 96, 99, 56, 57, 66, 67, 82}
        severe_alert = code in severe_codes

        # Summary text
        if code in severe_codes:
            summary = "Thunderstorm or heavy precipitation."
        elif code in {51, 52, 53, 61, 63, 65, 80, 81}:
            summary = f"Rain, {tm:.0f}°C. Rain probability {rain_p*100:.0f}%."
        elif code in {71, 73, 75, 77, 85, 86}:
            summary = f"Snow/cold, {tm:.0f}°C."
        elif code in {0}:
            summary = f"Clear, {tm:.0f}°C."
        elif code in {1, 2, 3}:
            summary = f"Partly cloudy, {tm:.0f}°C."
        elif code in {45, 48}:
            summary = f"Fog, {tm:.0f}°C."
        else:
            summary = f"Cloudy, {tm:.0f}°C. Rain probability {rain_p*100:.0f}%."

        return GetWeatherOutput(
            forecast_summary=summary,
            rain_probability=rain_p,
            severe_alert=severe_alert,
        )
    except Exception:
        return None


# --- Frankfurter (exchange rate) ---
def frankfurter_rate(base: str, quote: str) -> CurrencyFxOutput | None:
    """Fetch exchange rate from Frankfurter. No API key. Returns None on error."""
    try:
        base = (base or "USD").strip().upper()[:3]
        quote = (quote or "VND").strip().upper()[:3]
        r = requests.get(
            "https://api.frankfurter.app/latest",
            params={"from": base, "to": quote},
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        rate = (data.get("rates") or {}).get(quote)
        if rate is None:
            return None
        return CurrencyFxOutput(
            base=base,
            quote=quote,
            rate=float(rate),
            as_of=data.get("date", ""),
        )
    except Exception:
        return None


# --- Amadeus (flights + hotels) ---
def _amadeus_token() -> str | None:
    client_id = os.environ.get("AMADEUS_CLIENT_ID", "").strip()
    client_secret = os.environ.get("AMADEUS_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        return None
    try:
        r = requests.post(
            "https://api.amadeus.com/v1/security/oauth2/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        return r.json().get("access_token")
    except Exception:
        return None


def _city_to_iata(city: str) -> str | None:
    n = _norm_city(city)
    for key, code in CITY_TO_IATA.items():
        if key in n or n in key:
            return code
    if len(n) >= 3:
        return n[:3].upper()
    return None


def amadeus_flight_offers(
    origin: str, destination: str, departure_date: str
) -> list[TransportOption] | None:
    """Amadeus Flight Offers Search. Needs AMADEUS_CLIENT_ID + AMADEUS_CLIENT_SECRET."""
    token = _amadeus_token()
    if not token:
        return None
    orig_code = _city_to_iata(origin) or "HAN"
    dest_code = _city_to_iata(destination) or "DAD"
    date = _extract_first_date(departure_date) or datetime.now().strftime("%Y-%m-%d")
    try:
        r = requests.get(
            "https://api.amadeus.com/v2/shopping/flight-offers",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "originLocationCode": orig_code,
                "destinationLocationCode": dest_code,
                "departureDate": date,
                "adults": 1,
            },
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        offers = data.get("data") or []
        options: list[TransportOption] = []
        for o in offers[:5]:
            price = float((o.get("price") or {}).get("total", 0) or 0)
            currency = (o.get("price") or {}).get("currency", "USD")
            # Assume VND if currency is USD, convert later or report as USD
            if currency == "USD":
                price_vnd = price * 25000  # approximate
            else:
                price_vnd = price
            duration = (o.get("itineraries") or [{}])[0].get("duration") or "PT1H30M"
            # Parse PT1H30M -> 1.5
            h = 0.0
            m = 0.0
            if "H" in duration:
                h = float(re.search(r"(\d+)H", duration).group(1) or 0)
            if "M" in duration:
                m = float(re.search(r"(\d+)M", duration).group(1) or 0)
            dur_hours = h + m / 60.0
            options.append(
                TransportOption(
                    mode="flight",
                    price_min=price_vnd,
                    price_max=price_vnd,
                    duration_hours=round(dur_hours, 1),
                )
            )
        if options:
            return options
        return None
    except Exception:
        return None


def amadeus_hotel_list(city_name: str, budget: float) -> SearchHotelsOutput | None:
    """Amadeus Hotel List by city. Returns hotel names; price from budget range. Needs Amadeus key."""
    token = _amadeus_token()
    if not token:
        return None
    city_code = _city_to_iata(city_name)
    if not city_code:
        return None
    try:
        r = requests.get(
            "https://api.amadeus.com/v1/reference-data/locations/hotels/by-city",
            headers={"Authorization": f"Bearer {token}"},
            params={"cityCode": city_code},
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        hotels_data = data.get("data") or []
        hotels: list[HotelItem] = []
        # Budget in VND per night; spread fake rating/price around budget
        for i, h in enumerate(hotels_data[:10]):
            name = (h.get("name") or f"Hotel {i+1}").strip()
            # No price in this API; use budget * (0.7 .. 1.2) and fake rating
            factor = 0.7 + (i % 5) * 0.1
            price = int(budget * factor) if budget > 0 else 500000
            hotels.append(
                HotelItem(
                    name=name,
                    price_per_night=float(price),
                    rating=round(3.5 + (i % 5) * 0.2, 1),
                    availability=True,
                )
            )
        if hotels:
            return SearchHotelsOutput(hotels=hotels)
        return None
    except Exception:
        return None


# --- HotelsAPI.com (alternative to Amadeus for hotels) ---
def hotels_api_com_search(city_name: str, budget: float, limit: int = 10) -> SearchHotelsOutput | None:
    """
    Search hotels by city via HotelsAPI.com. Needs HOTELS_API_KEY.
    Free tier: 500 req/month. No price in response; we estimate from budget.
    """
    key = os.environ.get("HOTELS_API_KEY", "").strip()
    if not key:
        return None
    city = (city_name or "").strip() or "Hanoi"
    try:
        r = requests.get(
            "https://api.hotels-api.com/v1/hotels/search",
            headers={"X-API-KEY": key},
            params={"city": city, "limit": limit},
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        if not data.get("success"):
            return None
        raw = data.get("data") or []
        hotels: list[HotelItem] = []
        for i, h in enumerate(raw[:limit]):
            name = (h.get("name") or f"Hotel {i+1}").strip()
            rating = int(h.get("rating") or 0)
            if rating <= 0:
                rating = 3
            # API doesn't return price; use budget band
            price = int(budget * (0.7 + (i % 5) * 0.1)) if budget > 0 else 500000
            hotels.append(
                HotelItem(
                    name=name,
                    price_per_night=float(price),
                    rating=float(min(5, max(0, rating))),
                    availability=True,
                )
            )
        if hotels:
            return SearchHotelsOutput(hotels=hotels)
        return None
    except Exception:
        return None


# --- AviationStack (alternative to Amadeus for flights — routes only, no prices) ---
def _parse_time(s: str) -> float:
    """Parse HH:MM:SS or HH:MM to fractional hours."""
    if not s:
        return 0.0
    parts = str(s).strip().split(":")
    h = int(parts[0]) if len(parts) > 0 else 0
    m = int(parts[1]) if len(parts) > 1 else 0
    return h + m / 60.0


def aviationstack_routes(
    origin: str, destination: str, _dates: str
) -> list[TransportOption] | None:
    """
    Get flight routes between origin and destination via AviationStack.
    Needs AVIATIONSTACK_ACCESS_KEY. Returns routes with duration; no price (use 0 or check airline).
    Routes endpoint is Basic plan and higher (free tier may not include it).
    """
    key = os.environ.get("AVIATIONSTACK_ACCESS_KEY", "").strip()
    if not key:
        return None
    orig_code = _city_to_iata(origin) or "HAN"
    dest_code = _city_to_iata(destination) or "DAD"
    try:
        r = requests.get(
            "https://api.aviationstack.com/v1/routes",
            params={
                "access_key": key,
                "dep_iata": orig_code,
                "arr_iata": dest_code,
                "limit": 10,
            },
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        raw = data.get("data") or []
        options: list[TransportOption] = []
        seen_airlines: set[str] = set()
        for item in raw[:5]:
            airline = (item.get("airline") or {}).get("name") or "Flight"
            dep = item.get("departure") or {}
            arr = item.get("arrival") or {}
            t1 = _parse_time(dep.get("time", ""))
            t2 = _parse_time(arr.get("time", ""))
            dur = t2 - t1 if t2 > t1 else (24 - t1 + t2)
            if dur <= 0:
                dur = 1.5
            key_airline = (airline or "").strip()
            if key_airline in seen_airlines:
                continue
            seen_airlines.add(key_airline)
            options.append(
                TransportOption(
                    mode="flight",
                    price_min=0.0,
                    price_max=0.0,
                    duration_hours=round(dur, 1),
                )
            )
        if options:
            return options
        return None
    except Exception:
        return None


# --- Web search (DuckDuckGo only, no key) ---
def duckduckgo_search(query: str, num: int = 5) -> list[dict[str, str]] | None:
    """
    Search the web via DuckDuckGo. No API key. Requires: pip install duckduckgo-search.
    Returns list of {title, link, snippet}.
    """
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num))
        out: list[dict[str, str]] = []
        for r in results:
            out.append({
                "title": (r.get("title") or "").strip(),
                "link": (r.get("href") or r.get("link") or "").strip(),
                "snippet": (r.get("body") or "").strip(),
            })
        return out if out else None
    except Exception:
        return None


def web_search_results(query: str, num_results: int = 5) -> list[dict[str, str]] | None:
    """
    Run web search via DuckDuckGo only (no API key). Requires: pip install duckduckgo-search.
    Returns list of {title, link, snippet} or None.
    """
    return duckduckgo_search(query, num_results)
