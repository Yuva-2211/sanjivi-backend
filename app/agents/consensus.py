"""
Consensus Agent.

Merges responses from all five AYUSH expert agents into a single
unified recommendation using the LLM as a synthesis engine.
"""

from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage
from tenacity import retry, retry_if_not_exception_type, stop_after_attempt, wait_exponential

from app.config import settings
from app.models.llm import call_llm, RateLimitError
from app.prompts.consensus_prompt import CONSENSUS_SYSTEM, CONSENSUS_USER
from app.schemas.chat import ConsensusResponse, ExpertResponse, YogaResponse
from app.utils.helpers import parse_json_response, strip_markdown
from app.utils.logger import get_logger

log = get_logger(__name__)


def _expert_summary(resp: ExpertResponse | None) -> str:
    """Produce a compact text summary of an expert response for the prompt."""
    if not resp:
        return "No response available."
    parts = []
    if resp.diagnosis:
        parts.append(f"Diagnosis: {resp.diagnosis}")
    if resp.recommendations:
        parts.append(f"Recommendations: {resp.recommendations}")
    if resp.herbs_or_remedies:
        parts.append(f"Remedies: {', '.join(resp.herbs_or_remedies[:5])}")
    if resp.diet:
        parts.append(f"Diet: {resp.diet}")
    return " | ".join(parts) if parts else "No response available."


def _yoga_summary(resp: YogaResponse | None) -> str:
    if not resp:
        return "No response available."
    parts = []
    if resp.poses:
        parts.append(f"Poses: {', '.join(resp.poses[:3])}")
    if resp.breathing_exercises:
        parts.append(f"Pranayama: {', '.join(resp.breathing_exercises[:3])}")
    if resp.lifestyle:
        parts.append(f"Lifestyle: {resp.lifestyle}")
    return " | ".join(parts) if parts else "No response available."


@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_not_exception_type(RateLimitError),
    reraise=True,
)
async def run_consensus_agent(
    query: str,
    ayurveda: ExpertResponse | None,
    siddha: ExpertResponse | None,
    unani: ExpertResponse | None,
    homeopathy: ExpertResponse | None,
    yoga: YogaResponse | None,
) -> ConsensusResponse:
    """
    Synthesise all five expert responses into a unified recommendation.
    """
    log.info("consensus_agent_start")

    messages = [
        SystemMessage(content=CONSENSUS_SYSTEM),
        HumanMessage(
            content=CONSENSUS_USER.format(
                query=query,
                ayurveda=_expert_summary(ayurveda),
                siddha=_expert_summary(siddha),
                unani=_expert_summary(unani),
                homeopathy=_expert_summary(homeopathy),
                yoga=_yoga_summary(yoga),
            )
        ),
    ]

    try:
        response = await call_llm(
            messages,
            model=settings.consensus_model,
            max_tokens=settings.consensus_max_tokens,
            lane="consensus",
        )
        parsed = parse_json_response(response.content)

        result = ConsensusResponse(
            unified_recommendation=strip_markdown(parsed.get("unified_recommendation", "")),
            common_themes=[strip_markdown(t) for t in parsed.get("common_themes", [])],
            conflicts_detected=[strip_markdown(c) for c in parsed.get("conflicts_detected", [])],
            ranked_advice=[strip_markdown(a) for a in parsed.get("ranked_advice", [])],
        )
        log.info("consensus_agent_done", themes=len(result.common_themes))
        return result

    except json.JSONDecodeError as exc:
        log.error("consensus_json_error", error=str(exc))
        return ConsensusResponse(
            unified_recommendation="Consensus synthesis encountered a parsing error.",
        )
    except Exception as exc:
        log.error("consensus_agent_error", error=str(exc))
        raise
