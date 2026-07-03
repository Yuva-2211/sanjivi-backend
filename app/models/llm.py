"""
LLM provider router — Groq and OpenRouter via LangChain.

Provider Assignment:
- Groq: Lightweight, latency-critical agents (Emergency Detection, Reviewer).
  Model: llama-3.1-8b-instant
- OpenRouter: Reasoning-heavy agents (Ayurveda, Siddha, Unani, Homeopathy, Yoga, Consensus).
  Model: openai/gpt-oss-120b:free

Concurrency & Rate Control:
Each type of LLM call has its own "lane" semaphore to prevent low-priority
expert calls from blocking high-priority emergency checks or post-processing.
All calls acquire BOTH the global semaphore and the lane-specific semaphore.
"""

from __future__ import annotations

import logging
import asyncio
import random
from functools import lru_cache
from typing import Any, Literal

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

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
# Models known NOT to support response_format={"type": "json_object"} via their provider.
# Listing them here avoids a wasted round-trip (try JSON → get 400 → retry text).
_JSON_MODE_UNSUPPORTED: set[str] = {
    "openai/gpt-oss-120b",
    "openai/gpt-oss-120b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
}

_json_mode_supported: dict[str, bool] = {
    m: False for m in _JSON_MODE_UNSUPPORTED
}

# ── OpenRouter Fallback Chain ─────────────────────────────────────────────────
# Models are tried in sequence when 429s are encountered.
# Each maps to a DIFFERENT upstream provider for independent rate-limit headroom.
# OpenInference → Venice → Avian/Google → Featherless/Mistral
OPENROUTER_FALLBACK_CHAIN: list[str] = [
    "openai/gpt-oss-120b:free",               # Primary    (OpenInference)
    "meta-llama/llama-3.3-70b-instruct:free", # Fallback 1 (Venice)
    "google/gemma-3-27b-it:free",             # Fallback 2 (Google / Avian)
    "mistralai/mistral-7b-instruct:free",     # Fallback 3 (Mistral / Featherless)
]

# Keep the alias for backward-compat with any external imports
OPENROUTER_FALLBACK_MODEL = OPENROUTER_FALLBACK_CHAIN[1]


class RateLimitError(Exception):
    """Raised when all retry attempts are exhausted due to 429 rate limiting."""
    pass


# ── Provider routing helper ───────────────────────────────────────────────────

def _get_provider_for_model(model_name: str) -> Literal["groq", "openrouter"]:
    """
    Determine the LLM provider based on the model name.
    Reasoning-heavy models map to OpenRouter; latency-critical map to Groq.
    """
    openrouter_models = {
        settings.ayurveda_model,
        settings.siddha_model,
        settings.unani_model,
        settings.homeopathy_model,
        settings.yoga_model,
        settings.consensus_model,
    }
    if model_name in openrouter_models or "/" in model_name:
        return "openrouter"
    return "groq"


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


def _build_chatopenrouter(
    model: str,
    max_tokens: int | None = None,
    response_format: dict | None = None,
) -> ChatOpenAI:
    max_tokens = max_tokens or 2048
    logger.debug(
        "openrouter_request",
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
        "openai_api_key": settings.openrouter_api_key,
        "openai_api_base": "https://openrouter.ai/api/v1",
        "timeout": settings.groq_timeout,
        "max_retries": 0,  # We handle retries ourselves in _invoke_with_retry
        "default_headers": {
            "HTTP-Referer": "https://sanjivi.ai",
            "X-Title": "Sanjivi AI",
        }
    }
    if response_format is not None:
        kwargs["response_format"] = response_format
    return ChatOpenAI(**kwargs)


@lru_cache(maxsize=128)
def get_groq_llm(model: str | None = None, max_tokens: int | None = None) -> ChatGroq:
    """Return a cached ChatGroq instance without JSON mode."""
    return _build_chatgroq(model, max_tokens, None)


@lru_cache(maxsize=128)
def get_groq_llm_json(model: str | None = None, max_tokens: int | None = None) -> ChatGroq:
    """Return a cached ChatGroq instance with JSON mode."""
    return _build_chatgroq(model, max_tokens, {"type": "json_object"})


@lru_cache(maxsize=128)
def get_openrouter_llm(model: str, max_tokens: int | None = None) -> ChatOpenAI:
    """Return a cached ChatOpenAI instance for OpenRouter without JSON mode."""
    return _build_chatopenrouter(model, max_tokens, None)


@lru_cache(maxsize=128)
def get_openrouter_llm_json(model: str, max_tokens: int | None = None) -> ChatOpenAI:
    """Return a cached ChatOpenAI instance for OpenRouter with JSON mode."""
    return _build_chatopenrouter(model, max_tokens, {"type": "json_object"})


def get_llm(model: str | None = None, max_tokens: int | None = None) -> ChatGroq:
    """Return a cached ChatGroq instance without JSON mode (backward compatibility)."""
    return get_groq_llm(model, max_tokens)


def get_llm_json(model: str | None = None, max_tokens: int | None = None) -> ChatGroq:
    """Return a cached ChatGroq instance with JSON mode (backward compatibility)."""
    return get_groq_llm_json(model, max_tokens)


# ── Invocation and Retry Policy ───────────────────────────────────────────────

async def _invoke_with_retry(llm: Any, msgs: list[BaseMessage], model_name: str) -> Any:
    """
    Invoke Groq or OpenRouter via LangChain with custom exponential backoff on 429 rate limits.
    Raises RateLimitError if all retries are exhausted due to rate limits.
    Raises the original exception for all other errors.
    """
    max_attempts = settings.groq_max_retries + 1  # includes the first try
    base = settings.groq_backoff_base
    last_exc: Exception | None = None

    for attempt in range(max_attempts):
        try:
            return await llm.ainvoke(msgs)
        except Exception as exc:
            err_str = str(exc).lower()
            is_rate_limit = any(
                phrase in err_str
                for phrase in ("429", "rate limit", "too many requests", "rate_limit")
            )
            if is_rate_limit:
                last_exc = exc
                if attempt < max_attempts - 1:
                    # Honor the Retry-After header if the provider sends one
                    retry_after: float | None = None
                    try:
                        import re as _re
                        m = _re.search(r"retry_after_seconds[^:]*:\s*([\d.]+)", str(exc))
                        if m:
                            retry_after = float(m.group(1))
                    except Exception:
                        pass

                    if retry_after is not None:
                        wait_time = retry_after + random.uniform(0.5, 2.0)
                    else:
                        wait_time = (base ** (attempt + 1)) + random.uniform(0.3, 1.0)

                    logger.warning(
                        "llm_rate_limit_hit",
                        extra={
                            "model": model_name,
                            "attempt": attempt + 1,
                            "wait_time": round(wait_time, 2),
                            "retry_after_header": retry_after,
                            "error": str(exc)[:200],
                        },
                    )
                    await asyncio.sleep(wait_time)
                    continue
                # All attempts exhausted — raise sentinel so caller can try fallback
                raise RateLimitError(f"All {max_attempts} attempts rate-limited for {model_name}: {exc}") from exc
            else:
                raise

    raise RateLimitError(f"All {max_attempts} attempts rate-limited for {model_name}")


async def _invoke_openrouter_with_fallback(
    msgs: list[BaseMessage],
    primary_model: str,
    max_tokens: int | None,
    use_json: bool,
) -> Any:
    """
    Try each model in the OpenRouter fallback chain in order.
    If a model returns a 429 RateLimitError, the next model in the chain is tried.
    Raises RateLimitError only if every model in the chain is exhausted.
    """
    # Build the chain starting from the primary model, then any remaining fallbacks
    chain = [primary_model] + [
        m for m in OPENROUTER_FALLBACK_CHAIN if m != primary_model
    ]

    for idx, model_name in enumerate(chain):
        try:
            if use_json and _json_mode_supported.get(model_name, True):
                llm = get_openrouter_llm_json(model_name, max_tokens)
            else:
                llm = get_openrouter_llm(model_name, max_tokens)
            result = await _invoke_with_retry(llm, msgs, model_name)
            if idx > 0:
                logger.info(
                    "openrouter_fallback_success",
                    extra={"model_used": model_name, "position_in_chain": idx},
                )
            return result
        except RateLimitError:
            remaining = chain[idx + 1:]
            if remaining:
                logger.warning(
                    "openrouter_model_ratelimited_trying_next",
                    extra={"failed": model_name, "next": remaining[0], "remaining": len(remaining)},
                )
                continue
            # All models exhausted
            raise RateLimitError(
                f"All {len(chain)} OpenRouter fallback models are rate-limited: {chain}"
            )


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
    Invoke Groq or OpenRouter with JSON mode first, falling back to plain text on failure.

    Parameters
    ----------
    lane : "expert" | "emergency" | "consensus" | "reviewer"
        Controls which category semaphore is acquired in addition to the
        global semaphore, preventing lower-priority calls from blocking
        high-priority emergency screening.
    """
    model_for_log = model or settings.groq_model
    max_tokens_for_log = max_tokens or 2048
    provider = _get_provider_for_model(model_for_log)

    logger.debug(
        "llm_call",
        extra={
            "model": model_for_log,
            "provider": provider,
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
                        "llm_json_mode_skip",
                        extra={"model": model_for_log, "reason": "previous json mode failure"},
                    )
                else:
                    try:
                        if provider == "openrouter":
                            llm = get_openrouter_llm_json(model_for_log, max_tokens)
                        else:
                            llm = get_groq_llm_json(model_for_log, max_tokens)

                        response = await _invoke_with_retry(llm, messages, model_for_log)
                        logger.info(
                            "llm_call_success",
                            extra={"mode": "json", "model": model_for_log, "provider": provider, "lane": lane},
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
                            "llm_json_mode_disabled",
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

            if provider == "openrouter":
                # Use fallback chain: primary model → backup model on 429
                response = await _invoke_openrouter_with_fallback(
                    modified_messages, model_for_log, max_tokens, use_json=False
                )
            else:
                llm = get_groq_llm(model_for_log, max_tokens)
                response = await _invoke_with_retry(llm, modified_messages, model_for_log)

            # If the text-mode response doesn't parse as JSON, retry once with an
            # explicit repair instruction before giving up and returning raw output.
            if force_json:
                parsed = parse_json_response(response.content)
                if not parsed:
                    logger.info("llm_json_repair_retry", extra={"model": model_for_log})
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
                    if provider == "openrouter":
                        response = await _invoke_openrouter_with_fallback(
                            repair_messages, model_for_log, max_tokens, use_json=False
                        )
                    else:
                        llm = get_groq_llm(model_for_log, max_tokens)
                        response = await _invoke_with_retry(llm, repair_messages, model_for_log)

    logger.info(
        "llm_call_success",
        extra={"mode": "text", "model": model_for_log, "provider": provider, "lane": lane},
    )
    return response

