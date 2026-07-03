"""
LLM provider — Groq via LangChain.

Concurrency architecture
========================
Each type of Groq call has its own "lane" semaphore to prevent low-priority
expert calls from blocking high-priority emergency checks or post-processing:

  _global_semaphore   → hard cap on total concurrent Groq API requests
  _expert_semaphore   → throttles the 5 domain expert agents
  _emergency_semaphore → reserved lane for emergency screening (never blocked)
  _consensus_semaphore → post-processing, runs only after experts finish
  _reviewer_semaphore  → final safety check, runs only after consensus

Every LLM call must acquire BOTH _global_semaphore and its category semaphore.
This ensures type-level isolation while also respecting the global rate limit.

Retry policy
============
3 attempts with exponential backoff: base^1, base^2, base^3
Default base = 2 → waits: 2s, 4s, 8s (max 14s before giving up)
"""

from __future__ import annotations

import logging
import asyncio
import random
from functools import lru_cache
from typing import Any, Literal

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq

from app.config import settings
from app.utils.helpers import parse_json_response


logger = logging.getLogger(__name__)

# ── Semaphore setup ───────────────────────────────────────────────────────────
# Initialised lazily on first use so that settings are loaded first.
# Each agent category has its own lane; all share the global cap.

_global_semaphore: asyncio.Semaphore | None = None
_expert_semaphore: asyncio.Semaphore | None = None
_emergency_semaphore: asyncio.Semaphore | None = None
_consensus_semaphore: asyncio.Semaphore | None = None
_reviewer_semaphore: asyncio.Semaphore | None = None


def _get_semaphores() -> tuple[
    asyncio.Semaphore,
    asyncio.Semaphore,
    asyncio.Semaphore,
    asyncio.Semaphore,
    asyncio.Semaphore,
]:
    """Lazily initialise semaphores from settings (once per process)."""
    global _global_semaphore, _expert_semaphore, _emergency_semaphore
    global _consensus_semaphore, _reviewer_semaphore

    if _global_semaphore is None:
        _global_semaphore    = asyncio.Semaphore(settings.max_concurrent_global)
        _expert_semaphore    = asyncio.Semaphore(settings.max_concurrent_experts)
        _emergency_semaphore = asyncio.Semaphore(1)
        _consensus_semaphore = asyncio.Semaphore(1)
        _reviewer_semaphore  = asyncio.Semaphore(1)

    return (
        _global_semaphore,
        _expert_semaphore,
        _emergency_semaphore,
        _consensus_semaphore,
        _reviewer_semaphore,
    )


# ── JSON mode tracking ────────────────────────────────────────────────────────
# Models known NOT to support response_format={"type": "json_object"} via Groq.
# Listing them here avoids a wasted round-trip (try JSON → get 400 → retry text).
_JSON_MODE_UNSUPPORTED: set[str] = {
    "openai/gpt-oss-120b",
}

_json_mode_supported: dict[str, bool] = {
    m: False for m in _JSON_MODE_UNSUPPORTED
}


# ── Retry helper ──────────────────────────────────────────────────────────────

async def _invoke_with_retry(llm: ChatGroq, msgs: list[BaseMessage], model_name: str) -> Any:
    """
    Invoke Groq with exponential backoff on 429 (Rate Limit) errors.

    Retry policy: 3 attempts, backoff = base^attempt + jitter
      Attempt 1 → wait  2 + jitter
      Attempt 2 → wait  4 + jitter
      Attempt 3 → wait  8 + jitter
    Max total wait ≈ 14 seconds — well inside the 28s expert timeout.
    """
    max_attempts = settings.groq_max_retries + 1  # includes the first try
    base = settings.groq_backoff_base

    for attempt in range(max_attempts):
        try:
            return await llm.ainvoke(msgs)
        except Exception as exc:
            err_str = str(exc).lower()
            is_rate_limit = any(
                phrase in err_str
                for phrase in ("429", "rate limit", "too many requests", "rate_limit")
            )
            if is_rate_limit and attempt < max_attempts - 1:
                wait_time = (base ** (attempt + 1)) + random.uniform(0.3, 1.0)
                logger.warning(
                    "groq_rate_limit_hit",
                    extra={
                        "model": model_name,
                        "attempt": attempt + 1,
                        "wait_time": round(wait_time, 2),
                        "error": str(exc)[:200],
                    },
                )
                await asyncio.sleep(wait_time)
            else:
                raise
    # Final attempt (should not reach here, but for safety)
    return await llm.ainvoke(msgs)


# ── LLM builders ─────────────────────────────────────────────────────────────

def _build_chatgroq(
    model: str | None = None,
    max_tokens: int | None = None,
    response_format: dict | None = None,
) -> ChatGroq:
    model = model or settings.groq_model
    max_tokens = max_tokens or 2048
    logger.debug(
        "groq_request",
        extra={
            "model": model,
            "response_format": response_format,
            "max_tokens": max_tokens,
            "temperature": 0.1,
        },
    )
    kwargs: dict[str, Any] = {
        "model": model,
        "temperature": 0.1,
        "max_tokens": max_tokens,
        "api_key": settings.groq_api_key,
        "timeout": settings.groq_timeout,
        "max_retries": 0,  # We handle retries ourselves in _invoke_with_retry
    }
    if response_format is not None:
        kwargs["model_kwargs"] = {"response_format": response_format}
    return ChatGroq(**kwargs)


@lru_cache(maxsize=32)
def get_llm(model: str | None = None, max_tokens: int | None = None) -> ChatGroq:
    """Return a cached ChatGroq instance without JSON mode."""
    return _build_chatgroq(model, max_tokens, None)


@lru_cache(maxsize=32)
def get_llm_json(
    model: str | None = None, max_tokens: int | None = None
) -> ChatGroq:
    """Return a cached ChatGroq instance with JSON mode."""
    return _build_chatgroq(model, max_tokens, {"type": "json_object"})


# ── Public call_llm ───────────────────────────────────────────────────────────

# Lane identifiers — passed by each agent type
CallLane = Literal["expert", "emergency", "consensus", "reviewer"]


async def call_llm(
    messages: list[BaseMessage],
    model: str | None = None,
    max_tokens: int | None = None,
    force_json: bool = True,
    lane: CallLane = "expert",
) -> Any:
    """
    Invoke Groq with JSON mode first, falling back to plain text on failure.

    Parameters
    ----------
    lane : "expert" | "emergency" | "consensus" | "reviewer"
        Controls which category semaphore is acquired in addition to the
        global semaphore, preventing lower-priority calls from blocking
        high-priority emergency screening.
    """
    model_for_log = model or settings.groq_model
    max_tokens_for_log = max_tokens or 2048
    logger.debug(
        "groq_call",
        extra={
            "model": model_for_log,
            "max_tokens": max_tokens_for_log,
            "lane": lane,
            "messages": str(messages)[:2000],
        },
    )

    global_sem, expert_sem, emergency_sem, consensus_sem, reviewer_sem = _get_semaphores()

    lane_sem_map: dict[str, asyncio.Semaphore] = {
        "expert":    expert_sem,
        "emergency": emergency_sem,
        "consensus": consensus_sem,
        "reviewer":  reviewer_sem,
    }
    lane_sem = lane_sem_map.get(lane, expert_sem)

    # Acquire both semaphores — global first (outer), then lane-specific (inner).
    # This preserves lane isolation while enforcing the total concurrent request cap.
    async with global_sem:
        async with lane_sem:
            if force_json:
                if not _json_mode_supported.get(model_for_log, True):
                    logger.info(
                        "groq_json_mode_skip",
                        extra={"model": model_for_log, "reason": "previous json mode failure"},
                    )
                else:
                    try:
                        llm = get_llm_json(model, max_tokens)
                        response = await _invoke_with_retry(llm, messages, model_for_log)
                        logger.info(
                            "groq_call_success",
                            extra={"mode": "json", "model": model_for_log, "lane": lane},
                        )
                        return response
                    except Exception as exc:
                        reason = str(exc).lower()
                        if any(
                            keyword in reason
                            for keyword in ("response_format", "json", "validate", "bad request", "unsupported", "invalid")
                        ):
                            _json_mode_supported[model_for_log] = False
                        logger.info(
                            "groq_json_mode_disabled",
                            extra={"model": model_for_log, "error": str(exc)[:300]},
                        )

            modified_messages = messages
            if force_json and not _json_mode_supported.get(model_for_log, True):
                strict_instruction = (
                    "\n\nIMPORTANT: You MUST respond with ONLY a single valid JSON object. "
                    "Do not include any markdown formatting or code fences (e.g. ```json or ```), "
                    "no conversational prose, and no introductory/concluding text. Output raw JSON only."
                )
                if messages:
                    last_msg = messages[-1]
                    if isinstance(last_msg, HumanMessage):
                        modified_messages = messages[:-1] + [HumanMessage(content=last_msg.content + strict_instruction)]
                    elif isinstance(last_msg, SystemMessage):
                        modified_messages = messages[:-1] + [SystemMessage(content=last_msg.content + strict_instruction)]

            llm = get_llm(model, max_tokens)
            response = await _invoke_with_retry(llm, modified_messages, model_for_log)

            # If the text-mode response doesn't parse as JSON, retry once with an
            # explicit repair instruction before giving up and returning raw output.
            if force_json:
                parsed = parse_json_response(response.content)
                if not parsed:
                    logger.info("groq_json_repair_retry", extra={"model": model_for_log})
                    repair_messages = messages + [
                        AIMessage(content=response.content),
                        HumanMessage(
                            content=(
                                "Your previous response was not valid JSON. "
                                "Respond again with ONLY a single valid JSON object, "
                                "no prose, no markdown fences, no text before or after it."
                            )
                        )
                    ]
                    response = await _invoke_with_retry(llm, repair_messages, model_for_log)

    logger.info(
        "groq_call_success",
        extra={"mode": "text", "model": model_for_log, "lane": lane},
    )
    return response
