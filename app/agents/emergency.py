"""
Emergency Screening Agent.

Detects life-threatening conditions in the patient query.
If an emergency is found, fetches nearby hospitals using the
Google Places API and returns a structured HospitalReferral.
"""

from __future__ import annotations

from typing import Optional
from urllib.parse import quote_plus

import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from tenacity import retry, stop_after_attempt, wait_fixed

from app.config import settings
from app.models.llm import call_llm
from app.prompts.emergency_prompt import EMERGENCY_SYSTEM, EMERGENCY_USER
from app.schemas.chat import HospitalInfo, HospitalReferral
from app.utils.helpers import parse_json_response
from app.utils.logger import get_logger

log = get_logger(__name__)

# pyrefly: ignore [missing-import]
from duckduckgo_search import DDGS

# ── Hospital lookup ───────────────────────────────────────────────────────────

async def _fetch_nearby_hospitals(
    lat: float,
    lng: float,
    radius_m: int = 5000,
    max_results: int = 4,
) -> list[HospitalInfo]:
    """Return nearby hospital options with reliable map links."""
    maps_query = quote_plus(f"emergency hospitals near {lat},{lng}")
    hospitals: list[HospitalInfo] = [
        HospitalInfo(
            name="Nearby emergency hospitals",
            address="Open the map link to see hospitals closest to your current location.",
            phone=None,
            distance_km=None,
            maps_url=f"https://www.google.com/maps/search/?api=1&query={maps_query}",
        )
    ]

    try:
        query = f"hospital emergency near {lat},{lng}"
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

            for place in results:
                title = place.get("title") or "Hospital search result"
                href = place.get("href") or f"https://www.google.com/maps/search/?api=1&query={quote_plus(title)}"
                body = place.get("body") or "Open this result for hospital details."

                hospitals.append(
                    HospitalInfo(
                        name=title,
                        address=body,
                        phone=None,
                        distance_km=None,
                        maps_url=href,
                    )
                )
    except Exception as exc:
        log.error("hospital_search_error", error=str(exc))

    return hospitals[:max_results]


# ── LLM screening ─────────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
async def screen_for_emergency(
    query: str,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
) -> tuple[bool, Optional[HospitalReferral]]:
    """
    Analyse the query for emergency conditions.

    Returns:
        (is_emergency: bool, hospital_referral: HospitalReferral | None)

    If emergency=True and lat/lng provided → fetches nearby hospitals.
    If emergency=True without lat/lng → returns generic referral message.
    """
    messages = [
        SystemMessage(content=EMERGENCY_SYSTEM),
        HumanMessage(content=EMERGENCY_USER.format(query=query)),
    ]

    try:
        response = await call_llm(
            messages,
            model=settings.emergency_model,
            max_tokens=settings.emergency_max_tokens,
            force_json=True,
        )
        raw = response.content
        parsed = parse_json_response(raw)
        is_emergency = bool(parsed.get("emergency", False))
        reason = parsed.get("reason", "")

        log.info("emergency_screen", is_emergency=is_emergency, reason=reason[:100])

        if not is_emergency:
            return False, None

        hospitals: list[HospitalInfo] = []
        if lat is not None and lng is not None:
            hospitals = await _fetch_nearby_hospitals(lat, lng)

        if hospitals:
            nearest_hospital = hospitals[0]
            message = (
                f"This appears to be a medical emergency. {reason} "
                "Please go to the nearest hospital immediately or call emergency services. "
                f"Nearest hospital details are below: {nearest_hospital.name}. "
                "Call 112 for emergency services."
            )
        else:
            message = (
                f"This appears to be a medical emergency. {reason} "
                "Please call 112 or go to the nearest hospital emergency room immediately. "
                "Do not delay seeking in-person medical care. "
                "AYUSH therapies are not appropriate for acute emergencies."
            )

        referral = HospitalReferral(
            message=message,
            hospitals=hospitals,
            nearest_hospital=hospitals[0] if hospitals else None,
            emergency_number="112",
        )
        return True, referral

    except ValueError as exc:
        log.error("emergency_json_parse_error", error=str(exc), raw=raw[:200])
        return False, None
    except Exception as exc:
        log.error("emergency_screen_error", error=str(exc))
        return False, None
