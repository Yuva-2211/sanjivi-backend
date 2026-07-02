"""
General-purpose helpers used across the backend.
"""

from __future__ import annotations

import json
import re
import unicodedata
from typing import Any

from pydantic import BaseModel

from app.utils.exceptions import JSONParsingError


def clean_text(text: str) -> str:
    """
    Normalise extracted PDF/TXT text.

    Steps:
    1. Unicode NFKC normalisation (fixes ligatures, wide chars, etc.)
    2. Replace exotic whitespace with a plain space.
    3. Collapse runs of more than two consecutive newlines.
    4. Strip leading/trailing whitespace.
    """
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[^\S\n]", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def strip_markdown(text: str) -> str:
    """Remove markdown formatting artifacts from text."""
    if not text:
        return ""
    text = re.sub(r"\*{1,2}", "", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    disclaimer = "Please consult a qualified AYUSH practitioner before beginning any treatment."
    text = re.sub(r"(\s*" + re.escape(disclaimer) + r"\s*)+", " " + disclaimer + " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_json_object(raw: str) -> str:
    """Extract the first top-level JSON object from a noisy LLM response."""
    start = raw.find("{")
    if start == -1:
        raise ValueError("No JSON object found in response.")

    depth = 0
    for index, char in enumerate(raw[start:], start):
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return raw[start : index + 1]

    raise JSONParsingError("Incomplete JSON object in response.")


def parse_json_response(raw: str, model_cls: type[BaseModel] | None = None) -> dict[str, Any]:
    """Parse JSON from an LLM response, stripping fences and repairing malformed output."""
    text = raw.strip()

    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 3:
            text = "".join(parts[1:-1])
        else:
            text = "".join(parts[1:])
        text = text.strip()

    if text.lower().startswith("json"):
        text = text[4:]
        text = text.strip()

    if not text.startswith("{"):
        try:
            text = _extract_json_object(text)
        except Exception:
            text = "{" + text[text.find("}") + 1:] if "}" in text else text

    # Repair common malformed JSON
    text = re.sub(r",\s*}", "}", text)
    text = re.sub(r",\s*\]", "]", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"//.*$", "", text, flags=re.MULTILINE)

    def _try_parse(s: str) -> dict[str, Any] | None:
        try:
            data = json.loads(s)
            if model_cls is not None:
                try:
                    model_cls.model_validate(data)
                except Exception:
                    repaired = re.sub(r"(\w+)\s*:", r'"\1":', s)
                    data = json.loads(repaired)
            return data
        except (json.JSONDecodeError, Exception):
            return None

    data = _try_parse(text)
    if data is not None:
        return data

    # Retry once after attempting to isolate a JSON block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        candidate = re.sub(r",\s*}", "}", candidate)
        candidate = re.sub(r",\s*\]", "]", candidate)
        data = _try_parse(candidate)
        if data is not None:
            return data

    # Fallback JSON so callers never fail hard
    return {}


def llm_usage_metadata(response: Any) -> dict[str, Any]:
    """Extract token usage from a LangChain LLM response if available."""
    try:
        usage = response.usage
        return {
            "prompt_tokens": getattr(usage, "input_tokens", 0),
            "completion_tokens": getattr(usage, "output_tokens", 0),
            "total_tokens": getattr(usage, "total_tokens", 0),
        }
    except Exception:
        return {}


def normalize_confidence(value: Any, raw_response: str | None = None, default: float = 0.7) -> float:
    """Normalize confidence values and avoid silently returning 0.0 after a successful response."""
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        confidence = -1.0

    if 0.0 <= confidence <= 1.0:
        return confidence

    if raw_response and raw_response.strip():
        return min(max(default, 0.0), 1.0)

    return 0.0


def truncate(text: str, max_chars: int = 300) -> str:
    """Truncate text to max_chars with ellipsis."""
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_citation(source_file: str, page: int | None, domain: str, excerpt: str) -> dict:
    """Build a citation dict from chunk metadata."""
    citation = {
        "title": source_file,
        "page": page,
        "domain": domain,
        "excerpt": excerpt,
    }
    return citation
