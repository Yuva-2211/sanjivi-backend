"""
Emergency Screening Agent.

Detects life-threatening conditions in the patient query.
If an emergency is found, builds a reliable Google Maps URL anchored on the
user's GPS coordinates so the user can instantly see actual nearby hospitals.
No third-party scraping — just a precise, clickable maps link.
"""

from __future__ import annotations

from typing import Optional
from urllib.parse import quote_plus

from langchain_core.messages import HumanMessage, SystemMessage
from tenacity import retry, stop_after_attempt, wait_fixed

from app.config import settings
from app.models.llm import call_llm
from app.prompts.emergency_prompt import EMERGENCY_SYSTEM, EMERGENCY_USER
from app.schemas.chat import HospitalInfo, HospitalReferral
from app.utils.helpers import parse_json_response
from app.utils.logger import get_logger

log = get_logger(__name__)


# ── Hospital lookup ───────────────────────────────────────────────────────────

def _build_hospital_referral_from_location(
    lat: float,
    lng: float,
) -> list[HospitalInfo]:
    """
    Build reliable, location-anchored hospital entries using Google Maps search
    URLs pre-seeded with the user's GPS coordinates.

    This is more reliable than scraping or third-party APIs because:
    - Google Maps data is live and verified
    - The user's exact location is embedded in the search
    - Works globally without any API key
    """
    # Primary: search for emergency hospitals near the user's coordinates
    hospitals_search_url = (
        f"https://www.google.com/maps/search/emergency+hospital/"
        f"@{lat},{lng},14z"
    )

    # Directions to "hospital" from the user's current position
    # (Google Maps will pick the nearest one automatically)
    directions_url = (
        f"https://www.google.com/maps/dir/?api=1"
        f"&origin={lat},{lng}"
        f"&destination=hospital"
        f"&travelmode=driving"
    )

    return [
        HospitalInfo(
            name="Nearest Emergency Hospitals (map view)",
            address=(
                f"Tap 'Open map' to see all hospitals closest to your location "
                f"({round(lat, 4)}, {round(lng, 4)})."
            ),
            phone=None,
            distance_km=None,
            maps_url=hospitals_search_url,
        ),
        HospitalInfo(
            name="Get Directions to Nearest Hospital",
            address=(
                "Tap 'Open map' to get turn-by-turn driving directions "
                "to the nearest hospital from your current location."
            ),
            phone=None,
            distance_km=None,
            maps_url=directions_url,
        ),
    ]


def _build_generic_hospital_entry() -> list[HospitalInfo]:
    """Fallback when no coordinates are available."""
    return [
        HospitalInfo(
            name="Find Emergency Hospitals Near You",
            address=(
                "Allow browser location access and retry, "
                "or open the link to search for emergency hospitals on Google Maps."
            ),
            phone=None,
            distance_km=None,
            maps_url="https://www.google.com/maps/search/emergency+hospital+near+me",
        )
    ]


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

    If emergency=True and lat/lng provided → builds a location-anchored Google Maps entry.
    If emergency=True without lat/lng → returns a generic Google Maps search entry.
    """
    messages = [
        SystemMessage(content=EMERGENCY_SYSTEM),
        HumanMessage(content=EMERGENCY_USER.format(query=query)),
    ]

    raw = ""
    try:
        response = await call_llm(
            messages,
            model=settings.emergency_model,
            max_tokens=settings.emergency_max_tokens,
            force_json=True,
            lane="emergency",
        )
        raw = response.content
        parsed = parse_json_response(raw)
        is_emergency = bool(parsed.get("emergency", False))
        reason = parsed.get("reason", "")

        log.info("emergency_screen", is_emergency=is_emergency, reason=reason[:100])

        if not is_emergency:
            return False, None

        if lat is not None and lng is not None:
            hospitals = _build_hospital_referral_from_location(lat, lng)
            nearest = hospitals[0]
            message = (
                f"This appears to be a medical emergency. {reason} "
                "Please go to the nearest hospital immediately or call emergency services (112). "
                f"Use the map link below to find hospitals closest to your current location."
            )
        else:
            hospitals = _build_generic_hospital_entry()
            nearest = hospitals[0]
            message = (
                f"This appears to be a medical emergency. {reason} "
                "Please call 112 or go to the nearest hospital emergency room immediately. "
                "Do not delay seeking in-person medical care. "
                "AYUSH therapies are not appropriate for acute emergencies."
            )

        referral = HospitalReferral(
            message=message,
            hospitals=hospitals,
            nearest_hospital=nearest,
            emergency_number="112",
        )
        return True, referral

    except ValueError as exc:
        log.error("emergency_json_parse_error", error=str(exc), raw=raw[:200])
        return False, None
    except Exception as exc:
        log.error("emergency_screen_error", error=str(exc))
        return False, None
