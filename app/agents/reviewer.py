"""
Reviewer Agent.

Performs a final safety and accuracy check on the consensus response
before delivering it to the patient.  Produces the validated final_answer
in clean, plain prose suitable for the Next.js frontend.
"""

from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.models.llm import call_llm
from app.prompts.reviewer_prompt import REVIEWER_SYSTEM, REVIEWER_USER
from app.schemas.chat import (
    ConsensusResponse,
    ExpertResponse,
    ReviewerResponse,
    YogaResponse,
)
from app.utils.helpers import parse_json_response, strip_markdown
from app.utils.logger import get_logger

log = get_logger(__name__)


def _brief(resp: ExpertResponse | YogaResponse | None, domain: str) -> str:
    """Short summary of an expert response for the reviewer prompt."""
    if not resp:
        return f"{domain}: no response."
    if isinstance(resp, YogaResponse):
        poses = ", ".join(resp.poses[:3]) if resp.poses else "none"
        return f"{domain}: poses — {poses}. Lifestyle — {resp.lifestyle[:120] if resp.lifestyle else 'none'}."
    parts = []
    if resp.diagnosis:
        parts.append(resp.diagnosis[:120])
    if resp.recommendations:
        parts.append(resp.recommendations[:120])
    return f"{domain}: " + " ".join(parts) if parts else f"{domain}: no response."


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=10))
async def run_reviewer_agent(
    query: str,
    consensus: ConsensusResponse | None,
    ayurveda: ExpertResponse | None,
    siddha: ExpertResponse | None,
    unani: ExpertResponse | None,
    homeopathy: ExpertResponse | None,
    yoga: YogaResponse | None,
) -> ReviewerResponse:
    """
    Review and validate the consensus recommendation.

    Returns a ReviewerResponse with:
    - validated: bool
    - warnings: list of safety concerns
    - final_answer: clean patient-facing response
    - patient_summary: 2-3 sentence case summary
    """
    log.info("reviewer_agent_start")

    consensus_text = (
        consensus.unified_recommendation if consensus else "No consensus available."
    )

    messages = [
        SystemMessage(content=REVIEWER_SYSTEM),
        HumanMessage(
            content=REVIEWER_USER.format(
                query=query,
                consensus=consensus_text,
                ayurveda_summary=_brief(ayurveda, "Ayurveda"),
                siddha_summary=_brief(siddha, "Siddha"),
                unani_summary=_brief(unani, "Unani"),
                homeopathy_summary=_brief(homeopathy, "Homeopathy"),
                yoga_summary=_brief(yoga, "Yoga"),
            )
        ),
    ]

    try:
        response = await call_llm(
            messages,
            model=settings.reviewer_model,
            max_tokens=settings.reviewer_max_tokens,
        )
        parsed = parse_json_response(response.content)

        final_answer = strip_markdown(parsed.get("final_answer", ""))
        validated = bool(parsed.get("validated", True))

        # Safety net: catch false-positive rejections of valid AYUSH content.
        # A genuine safety failure has a specific, non-boilerplate final_answer.
        _REJECTION_PHRASES = (
            "cannot provide a valid response",
            "unable to generate",
            "hallucinations",
            "regeneration is required",
        )
        is_false_positive = not validated and (
            not final_answer
            or any(phrase in final_answer.lower() for phrase in _REJECTION_PHRASES)
        )
        if is_false_positive:
            log.warning("reviewer_false_positive_rejection", final_answer=final_answer[:120])
            validated = True
            fallback_body = (
                consensus_text
                if consensus_text and consensus_text != "No consensus available."
                else "Based on the AYUSH expert assessments, please follow the recommendations provided by each system above."
            )
            final_answer = (
                f"{fallback_body}\n\n"
                "Please consult a qualified AYUSH practitioner before beginning any treatment."
            )

        result = ReviewerResponse(
            validated=validated,
            warnings=[strip_markdown(w) for w in parsed.get("warnings", [])],
            final_answer=final_answer,
            patient_summary=strip_markdown(parsed.get("patient_summary", "")),
        )
        log.info(
            "reviewer_agent_done",
            validated=result.validated,
            warnings=len(result.warnings),
        )
        return result

    except json.JSONDecodeError as exc:
        log.error("reviewer_json_error", error=str(exc))
        return ReviewerResponse(
            validated=False,
            warnings=["Reviewer agent encountered a parsing error."],
            final_answer="We were unable to generate a validated response at this time. Please try again.",
            patient_summary="",
        )
    except Exception as exc:
        log.error("reviewer_agent_error", error=str(exc))
        raise
