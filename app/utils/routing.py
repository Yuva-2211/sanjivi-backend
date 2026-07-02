"""Query routing utilities for Sanjivi AI.

This module provides lightweight classification of user queries into
medical domains, with deterministic keyword mappings and a conservative
Multisystem fallback.
"""

from __future__ import annotations

import re
from typing import Iterable

VALID_SYSTEMS = [
    "Multisystem",
    "Ayurveda",
    "Siddha",
    "Unani",
    "Homeopathy",
    "Yoga",
]

DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "Ayurveda": [
        r"joint", r"stiff", r"pain", r"back pain", r"headache", r"migraine", r"stress",
        r"digest", r"constipation", r"diarrhea", r"nausea", r"acne",
        r"skin", r"women", r"menstrual", r"menopause", r"wellness",
        r"sleep", r"fatigue", r"anxiety", r"healthy", r"hair",
    ],
    "Siddha": [
        r"joint", r"stiff", r"back pain", r"headache", r"migraine", r"women", r"menstrual",
        r"menopause", r"skin", r"acne", r"wellness",
    ],
    "Unani": [
        r"digest", r"constipation", r"diarrhea", r"stomach", r"gas",
        r"acid reflux", r"cough", r"cold", r"asthma", r"breath", r"respiratory",
        r"sinus",
    ],
    "Homeopathy": [
        r"skin", r"acne", r"rash", r"eczema", r"dermatitis",
        r"homeopathy", r"remedy", r"potency",
    ],
    "Yoga": [
        r"stress", r"anxiety", r"sleep", r"fatigue", r"wellness", r"lifestyle",
        r"breath", r"pranayama", r"meditation", r"energy", r"stiff",
    ],
}

DEFAULT_DOMAIN = ["Multisystem"]


def normalize_selected_system(selected_system: str | None) -> str:
    if not selected_system or not isinstance(selected_system, str):
        return "Multisystem"
    normalized = selected_system.strip().title()
    if normalized == "Ayush":
        return "Multisystem"
    return normalized if normalized in VALID_SYSTEMS else "Multisystem"


def _matches_query(query: str, patterns: Iterable[str]) -> bool:
    lowered = query.lower()
    for pattern in patterns:
        if re.search(pattern, lowered):
            return True
    return False


def classify_query_domains(query: str) -> list[str]:
    """Classify a user query into one or more AYUSH domains."""
    if not query or not isinstance(query, str):
        return DEFAULT_DOMAIN

    normalized_query = " ".join(re.findall(r"[a-zA-Z0-9]+", query.lower()))
    if not normalized_query:
        return DEFAULT_DOMAIN

    selected: list[str] = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if _matches_query(normalized_query, keywords):
            selected.append(domain)

    if not selected:
        return DEFAULT_DOMAIN

    # Ensure Yoga and Ayurveda overlap for lifestyle/general wellness queries.
    if "Yoga" in selected and "Ayurveda" not in selected:
        if _matches_query(normalized_query, [r"wellness", r"lifestyle", r"healthy"]):
            selected.append("Ayurveda")

    # Do not randomly include Homeopathy unless a skin or explicitly homeopathic signal exists.
    if "Homeopathy" in selected and not _matches_query(
        normalized_query,
        [r"skin", r"acne", r"rash", r"eczema", r"homeopathy", r"potency"],
    ):
        selected.remove("Homeopathy")

    return selected if selected else DEFAULT_DOMAIN
