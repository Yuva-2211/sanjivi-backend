"""
Yoga Expert Agent.

Retrieves relevant chunks from the Yoga Pinecone namespace + BM25 index
using hybrid RRF, then calls the LLM with a Yoga-specific prompt.

Returns poses as a list of strings (used by the Yoga Image Search Agent
to fetch pose images).
"""

from __future__ import annotations

import json
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.models.llm import call_llm
from app.prompts.yoga_prompt import YOGA_SYSTEM, YOGA_USER
from app.rag.retriever import get_hybrid_retriever, build_context_string
from app.schemas.chat import YogaResponse
from app.schemas.rag import RetrievedChunk
from app.utils.helpers import parse_json_response, strip_markdown
from app.utils.logger import get_logger

log = get_logger(__name__)

DOMAIN = "yoga"


def _parse_yoga_response(raw: str) -> dict:
    return parse_json_response(raw)


def _build_yoga_response(parsed: dict) -> YogaResponse:
    return YogaResponse(
        poses=[strip_markdown(p) for p in parsed.get("poses", [])],
        breathing_exercises=[strip_markdown(b) for b in parsed.get("breathing_exercises", [])],
        lifestyle=strip_markdown(parsed.get("lifestyle", "")),
        images=[],  # Populated by yoga_image_search agent
    )


@retry(stop=stop_after_attempt(1), wait=wait_exponential(multiplier=1, min=2, max=10))
async def run_yoga_expert(
    query: str,
    chunks: list[RetrievedChunk] | None = None,
    history: list[dict] | None = None,
) -> tuple[Optional[YogaResponse], list[RetrievedChunk]]:
    """Run the Yoga expert agent."""
    log.info("yoga_expert_start", query=query[:80])

    if chunks is None:
        retriever = get_hybrid_retriever(DOMAIN)
        chunks = await retriever.retrieve(query)
    context = build_context_string(chunks)

    history_text = "None"
    if history:
        last_turns = history[-4:]
        history_text = "\n".join(
            f"{h['role'].capitalize()}: {h['content'][:200]}" for h in last_turns
        )

    if not context.strip():
        log.warning("yoga_no_context", query=query[:80])
        return (
            YogaResponse(
                poses=[],
                breathing_exercises=[],
                lifestyle="Insufficient Yoga literature was retrieved to address this query.",
            ),
            [],
        )

    messages = [
        SystemMessage(content=YOGA_SYSTEM),
        HumanMessage(content=YOGA_USER.format(query=query, context=context, history=history_text)),
    ]

    try:
        response = await call_llm(
            messages,
            model=settings.yoga_model,
            max_tokens=settings.yoga_max_tokens,
            lane="expert",
        )
        parsed = _parse_yoga_response(response.content)
        yoga_resp = _build_yoga_response(parsed)
        log.info("yoga_expert_done", poses=len(yoga_resp.poses))
        return yoga_resp, chunks
    except json.JSONDecodeError as exc:
        log.error("yoga_json_error", error=str(exc))
        return YogaResponse(lifestyle="Yoga expert encountered a parsing error."), chunks
    except Exception as exc:
        log.error("yoga_expert_error", error=str(exc))
        raise
