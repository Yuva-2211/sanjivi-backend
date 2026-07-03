"""Query routing utilities for Sanjivi AI.

Routing modes:
  - "Multisystem"  → Always run ALL 5 AYUSH experts (no routing needed)
  - "Auto"         → Router selects only the relevant experts for the query
  - any single system name → Run only that one expert
"""

from __future__ import annotations

import re
from typing import Iterable

VALID_SYSTEMS = [
    "Auto",
    "Multisystem",
    "Ayurveda",
    "Siddha",
    "Unani",
    "Homeopathy",
    "Yoga",
]

ALL_EXPERT_DOMAINS = ["Ayurveda", "Siddha", "Unani", "Homeopathy", "Yoga"]

# Broad keyword → domain mappings used by the Auto router.
# Intentionally inclusive: prefer false positives over missing a relevant system.
DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "Ayurveda": [
        r"joint", r"stiff", r"pain", r"back pain", r"headache", r"migraine", r"stress",
        r"digest", r"constipation", r"diarrhea", r"nausea", r"acne",
        r"skin", r"women", r"menstrual", r"menopause", r"wellness",
        r"sleep", r"fatigue", r"anxiety", r"healthy", r"hair",
        r"weight", r"liver", r"kidney", r"thyroid", r"sugar", r"diabetes",
        r"detox", r"immunity", r"fever", r"inflammation",
    ],
    "Siddha": [
        r"joint", r"stiff", r"back pain", r"headache", r"migraine",
        r"women", r"menstrual", r"menopause", r"skin", r"acne",
        r"wellness", r"fever", r"rheumatic", r"vatha", r"pitha", r"kabha",
        r"varma", r"thokkanam",
    ],
    "Unani": [
        r"digest", r"constipation", r"diarrhea", r"stomach", r"gas",
        r"acid reflux", r"cough", r"cold", r"asthma", r"breath", r"respiratory",
        r"sinus", r"liver", r"kidney", r"bladder", r"uti", r"infection",
        r"fever", r"inflammation", r"immune",
    ],
    "Homeopathy": [
        r"skin", r"acne", r"rash", r"eczema", r"dermatitis", r"allergy",
        r"homeopathy", r"remedy", r"potency", r"chronic", r"recurring",
        r"anxiety", r"depression", r"grief", r"sensitivity",
    ],
    "Yoga": [
        r"stress", r"anxiety", r"sleep", r"fatigue", r"wellness", r"lifestyle",
        r"breath", r"pranayama", r"meditation", r"energy", r"stiff",
        r"posture", r"flexibility", r"balance", r"pain", r"mental",
        r"depression", r"focus", r"weight",
    ],
}

DEFAULT_AUTO_DOMAINS = ALL_EXPERT_DOMAINS  # Fallback when classifier is unsure


def normalize_selected_system(selected_system: str | None) -> str:
    if not selected_system or not isinstance(selected_system, str):
        return "Auto"
    normalized = selected_system.strip().title()
    if normalized in ("Ayush",):
        return "Multisystem"
    return normalized if normalized in VALID_SYSTEMS else "Auto"


def _matches_query(query: str, patterns: Iterable[str]) -> bool:
    lowered = query.lower()
    for pattern in patterns:
        if re.search(pattern, lowered):
            return True
    return False


def classify_query_domains(query: str) -> list[str]:
    """
    Classify a user query into one or more AYUSH domains.

    This is used only in "Auto" mode. The classifier is intentionally
    broad: it selects every system that can provide meaningful input,
    not just the single "best" match.
    """
    if not query or not isinstance(query, str):
        return DEFAULT_AUTO_DOMAINS

    normalized_query = " ".join(re.findall(r"[a-zA-Z0-9]+", query.lower()))
    if not normalized_query:
        return DEFAULT_AUTO_DOMAINS

    selected: list[str] = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if _matches_query(normalized_query, keywords):
            selected.append(domain)

    if not selected:
        return DEFAULT_AUTO_DOMAINS

    # Ensure Yoga and Ayurveda always pair for lifestyle/wellness queries
    if "Yoga" in selected and "Ayurveda" not in selected:
        if _matches_query(normalized_query, [r"wellness", r"lifestyle", r"healthy", r"stress", r"pain"]):
            selected.append("Ayurveda")

    # Include Siddha alongside Ayurveda for common overlap conditions
    if "Ayurveda" in selected and "Siddha" not in selected:
        if _matches_query(normalized_query, [r"joint", r"stiff", r"pain", r"skin", r"fever", r"menstrual"]):
            selected.append("Siddha")

    return selected
