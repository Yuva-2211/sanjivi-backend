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

# Keep the alias for backward-compat with any external imports if needed
OPENROUTER_FALLBACK_MODEL = "meta-llama/llama-3.3-70b-instruct"


class RateLimitError(Exception):
    """Raised when all retry attempts are exhausted due to 429 rate limiting."""
    pass


# ── Provider routing helper ───────────────────────────────────────────────────

def _get_provider_for_model(model_name: str) -> Literal["groq", "openrouter"]:
    """
    Determine the LLM provider based on the model name's shape.
    OpenRouter slugs are always "namespace/model" (contain a slash).
    Groq model names never contain a slash.
    """
    return "openrouter" if "/" in model_name else "groq"


# ── LLM builders ─────────────────────────────────────────────────────────────

def _get_groq_api_key() -> str:
    """Get a Groq API key, rotating through groq_api_keys_str if provided, else using groq_api_key."""
    if settings.groq_api_keys_str:
        keys = [k.strip() for k in settings.groq_api_keys_str.split(",") if k.strip()]
        if keys:
            selected_key = random.choice(keys)
            logger.debug("rotating_groq_api_key", extra={"key_suffix": selected_key[-6:] if len(selected_key) > 6 else ""})
            return selected_key
    return settings.groq_api_key


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
    api_key = _get_groq_api_key()
    kwargs: dict[str, Any] = {
        "model": model,
        "temperature": 0.1,
        "max_tokens": max_tokens,
        "api_key": api_key,
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


def get_groq_llm(model: str | None = None, max_tokens: int | None = None) -> ChatGroq:
    """Return a fresh ChatGroq instance without JSON mode."""
    return _build_chatgroq(model, max_tokens, None)


def get_groq_llm_json(model: str | None = None, max_tokens: int | None = None) -> ChatGroq:
    """Return a fresh ChatGroq instance with JSON mode."""
    return _build_chatgroq(model, max_tokens, {"type": "json_object"})


def get_openrouter_llm(model: str, max_tokens: int | None = None) -> ChatOpenAI:
    """Return a fresh ChatOpenAI instance for OpenRouter without JSON mode."""
    return _build_chatopenrouter(model, max_tokens, None)


def get_openrouter_llm_json(model: str, max_tokens: int | None = None) -> ChatOpenAI:
    """Return a fresh ChatOpenAI instance for OpenRouter with JSON mode."""
    return _build_chatopenrouter(model, max_tokens, {"type": "json_object"})


def get_llm(model: str | None = None, max_tokens: int | None = None) -> ChatGroq:
    """Return a fresh ChatGroq instance without JSON mode (backward compatibility)."""
    return get_groq_llm(model, max_tokens)


def get_llm_json(model: str | None = None, max_tokens: int | None = None) -> ChatGroq:
    """Return a fresh ChatGroq instance with JSON mode (backward compatibility)."""
    return get_groq_llm_json(model, max_tokens)


# ── Invocation and Retry Policy ───────────────────────────────────────────────

async def _invoke_with_retry(llm: Any, msgs: list[BaseMessage], model_name: str) -> Any:
    """
    Invoke Groq or OpenRouter via LangChain with custom exponential backoff on 429 rate limits.
    If 'llm' is callable, it is called on each attempt to get a fresh instance (supporting key rotation).
    Raises RateLimitError if all retries are exhausted due to rate limits.
    Raises the original exception for all other errors.
    """
    provider = _get_provider_for_model(model_name)
    max_attempts = settings.groq_max_retries + 1  # same retry budget for both providers

    base = settings.groq_backoff_base
    last_exc: Exception | None = None

    for attempt in range(max_attempts):
        try:
            current_llm = llm() if callable(llm) else llm
            return await current_llm.ainvoke(msgs)
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
    Invoke Groq or OpenRouter. If OpenRouter is rate-limited (429), automatically
    fallback to Groq using settings.groq_model and rotated API keys.
    """
    primary_model = model or settings.groq_model
    primary_provider = _get_provider_for_model(primary_model)

    async def _execute_with_provider(model_name: str, prov: str) -> Any:
        if force_json:
            if not _json_mode_supported.get(model_name, True):
                logger.info(
                    "llm_json_mode_skip",
                    extra={"model": model_name, "reason": "previous json mode failure"},
                )
            else:
                try:
                    if prov == "openrouter":
                        llm_factory = lambda: get_openrouter_llm_json(model_name, max_tokens)
                    else:
                        llm_factory = lambda: get_groq_llm_json(model_name, max_tokens)

                    response = await _invoke_with_retry(llm_factory, messages, model_name)
                    logger.info(
                        "llm_call_success",
                        extra={"mode": "json", "model": model_name, "provider": prov, "lane": lane},
                    )
                    return response
                except RateLimitError:
                    raise
                except Exception as exc:
                    reason = str(exc).lower()
                    if any(
                        keyword in reason
                        for keyword in ("response_format", "json", "validate", "bad request", "unsupported", "invalid")
                    ):
                        _json_mode_supported[model_name] = False
                    logger.info(
                        "llm_json_mode_disabled",
                        extra={"model": model_name, "error": str(exc)[:300]},
                    )

        modified_messages = messages
        if force_json and not _json_mode_supported.get(model_name, True):
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

        if prov == "openrouter":
            llm_factory = lambda: get_openrouter_llm(model_name, max_tokens)
        else:
            llm_factory = lambda: get_groq_llm(model_name, max_tokens)

        response = await _invoke_with_retry(llm_factory, modified_messages, model_name)

        if force_json:
            parsed = parse_json_response(response.content)
            if not parsed:
                logger.info("llm_json_repair_retry", extra={"model": model_name})
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
                if prov == "openrouter":
                    llm_factory = lambda: get_openrouter_llm(model_name, max_tokens)
                else:
                    llm_factory = lambda: get_groq_llm(model_name, max_tokens)
                response = await _invoke_with_retry(llm_factory, repair_messages, model_name)

        logger.info(
            "llm_call_success",
            extra={"mode": "text", "model": model_name, "provider": prov, "lane": lane},
        )
        return response

    global_sem, expert_sem, emergency_sem, consensus_sem, reviewer_sem = _get_semaphores()
    lane_sem_map: dict[str, asyncio.Semaphore] = {
        "expert":    expert_sem,
        "emergency": emergency_sem,
        "consensus": consensus_sem,
        "reviewer":  reviewer_sem,
    }
    lane_sem = lane_sem_map.get(lane, expert_sem)

    async with global_sem:
        async with lane_sem:
            try:
                return await _execute_with_provider(primary_model, primary_provider)
            except RateLimitError as exc:
                if primary_provider == "openrouter":
                    fallback_model = settings.groq_model
                    logger.warning(
                        "openrouter_rate_limit_falling_back_to_groq",
                        extra={"original_model": primary_model, "fallback_model": fallback_model, "error": str(exc)},
                    )
                    try:
                        return await _execute_with_provider(fallback_model, "groq")
                    except RateLimitError:
                        logger.error("both_openrouter_and_groq_rate_limited", extra={"model": fallback_model})
                        return None
                    except Exception as fallback_exc:
                        logger.error("groq_fallback_failed", extra={"model": fallback_model, "error": str(fallback_exc)})
                        return None
                else:
                    logger.warning("Expert unavailable", extra={"model": primary_model})
                    return None

