"""
Ayurveda Expert Agent.

Retrieves relevant chunks from the Ayurveda Pinecone namespace + BM25 index
using hybrid RRF, then calls the LLM with an Ayurveda-specific prompt.
"""

from __future__ import annotations

import json
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from tenacity import retry, retry_if_not_exception_type, stop_after_attempt, wait_exponential

from app.config import settings
from app.models.llm import call_llm, RateLimitError
from app.prompts.ayurveda_prompt import AYURVEDA_SYSTEM, AYURVEDA_USER
from app.rag.retriever import get_hybrid_retriever, build_context_string
from app.schemas.chat import ExpertResponse
from app.schemas.rag import RetrievedChunk
from app.utils.helpers import parse_json_response, strip_markdown, normalize_confidence
from app.utils.logger import get_logger

log = get_logger(__name__)

DOMAIN = "ayurveda"


def _parse_expert_response(raw: str) -> dict:
    """Parse strict JSON from LLM output, removing any markdown fences."""
    return parse_json_response(raw)


def _build_expert_response(parsed: dict, raw_response: str) -> ExpertResponse:
    """Convert parsed dict to ExpertResponse, cleaning all text fields."""
    return ExpertResponse(
        diagnosis=strip_markdown(parsed.get("diagnosis", "")),
        recommendations=strip_markdown(parsed.get("recommendations", "")),
        herbs_or_remedies=[
            strip_markdown(h) for h in parsed.get("herbs_or_remedies", [])
        ],
        diet=strip_markdown(parsed.get("diet", "")),
        lifestyle=strip_markdown(parsed.get("lifestyle", "")),
        evidence=[strip_markdown(e) for e in parsed.get("evidence", [])],
        confidence=normalize_confidence(parsed.get("confidence"), raw_response=raw_response),
    )


@retry(
    stop=stop_after_attempt(1),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_not_exception_type(RateLimitError),
    reraise=True,
)
async def run_ayurveda_expert(
    query: str,
    chunks: list[RetrievedChunk] | None = None,
    history: list[dict] | None = None,
) -> tuple[Optional[ExpertResponse], list[RetrievedChunk]]:
    """
    Run the Ayurveda expert agent.

    Returns:
        (ExpertResponse, list[RetrievedChunk]) — response and source chunks for citations.
    """
    log.info("ayurveda_expert_start", query=query[:80])

    if chunks is None:
        retriever = get_hybrid_retriever(DOMAIN)
        chunks = await retriever.retrieve(query)
    context = build_context_string(chunks)

    # Format last 2 turns of conversation history as context
    history_text = "None"
    if history:
        last_turns = history[-4:]  # last 2 pairs = 4 messages max
        history_text = "\n".join(
            f"{h['role'].capitalize()}: {h['content'][:200]}" for h in last_turns
        )

    if not context.strip():
        log.warning("ayurveda_no_context", query=query[:80])
        return (
            ExpertResponse(
                diagnosis="Insufficient Ayurvedic literature was retrieved to address this query. Please ensure documents have been ingested.",
                confidence=0.0,
            ),
            [],
        )

    messages = [
        SystemMessage(content=AYURVEDA_SYSTEM),
        HumanMessage(content=AYURVEDA_USER.format(query=query, context=context, history=history_text)),
    ]

    try:
        response = await call_llm(
            messages,
            model=settings.ayurveda_model,
            max_tokens=settings.ayurveda_max_tokens,
            lane="expert",
        )
        if response is None:
            return None, chunks
        parsed = _parse_expert_response(response.content)
        expert_resp = _build_expert_response(parsed, response.content)
        log.info("ayurveda_expert_done", confidence=expert_resp.confidence)
        return expert_resp, chunks
    except json.JSONDecodeError as exc:
        log.error("ayurveda_json_error", error=str(exc))
        return (
            ExpertResponse(
                diagnosis="Ayurveda expert encountered a response parsing error.",
                confidence=0.0,
            ),
            chunks,
        )
    except Exception as exc:
        log.error("ayurveda_expert_error", error=str(exc))
        raise
