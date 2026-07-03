"""
LLM provider — Groq via LangChain.

Concurrency & Key Rotation Architecture
=======================================
Each type of Groq call has its own "lane" semaphore to prevent low-priority
expert calls from blocking high-priority emergency checks or post-processing:

  _global_semaphore    → hard cap on total concurrent Groq API requests
  _expert_semaphore    → throttles the 5 domain expert agents
  _emergency_semaphore → reserved lane for emergency screening (never blocked)
  _consensus_semaphore → post-processing, runs only after experts finish
  _reviewer_semaphore  → final safety check, runs only after consensus

Every LLM call must acquire BOTH _global_semaphore and its category semaphore.
This ensures type-level isolation while also respecting the global rate limit.

Key Rotation (wiser scheduling)
===============================
Supports multi-key rotation via `GROQ_API_KEYS_STR` to completely bypass 429 rate
limits. If a key hits a 429:
  1. The key is put on a temporary cooldown (e.g. 45 seconds).
  2. The manager immediately selects the next healthy, non-cooldown key.
  3. The request is retried with the new key immediately without sleeping.
  4. If all keys are on cooldown, the system pauses until the first key recovers.
"""

from __future__ import annotations

import logging
import asyncio
import random
import time
from functools import lru_cache
from typing import Any, Literal

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq

from app.config import settings
from app.utils.helpers import parse_json_response


logger = logging.getLogger(__name__)

# ── Key Manager ───────────────────────────────────────────────────────────────

class GroqKeyManager:
    """
    Manages a pool of Groq API keys, tracking rate limits (cooldowns)
    and scheduling keys to maximize concurrency and avoid 429s.
    """
    def __init__(self):
        self._keys: list[str] = []
        self._cooldowns: dict[str, float] = {}
        self._current_idx: int = 0
        self._lock = asyncio.Lock()

    def initialize(self, keys: list[str]):
        self._keys = keys
        self._cooldowns = {k: 0.0 for k in keys}

    async def get_key_info(self) -> tuple[str, float]:
        """
        Selects the next available key (round-robin among healthy keys).
        If all keys are on cooldown, returns the key that recovers earliest
        along with its recovery timestamp.
        """
        async with self._lock:
            if not self._keys:
                raise ValueError("No Groq API keys are configured.")

            now = time.time()
            # Filter for keys that are not currently in cooldown
            healthy_keys = [k for k in self._keys if self._cooldowns[k] <= now]

            if healthy_keys:
                # Round-robin distribution
                key = healthy_keys[self._current_idx % len(healthy_keys)]
                self._current_idx = (self._current_idx + 1) % len(healthy_keys)
                return key, 0.0

            # All keys are in cooldown; pick the one recovering earliest
            earliest_key = min(self._keys, key=lambda k: self._cooldowns[k])
            return earliest_key, self._cooldowns[earliest_key]

    async def mark_cooldown(self, key: str, duration: float = 45.0):
        """Mark a key as rate-limited with a cooldown duration."""
        async with self._lock:
            if key in self._cooldowns:
                self._cooldowns[key] = time.time() + duration
                logger.info(
                    "groq_key_cooldown_set",
                    extra={"key_suffix": key[-6:], "duration": duration}
                )

_key_manager = GroqKeyManager()
_key_manager_initialized = False


def _get_key_manager() -> GroqKeyManager:
    global _key_manager_initialized
    if not _key_manager_initialized:
        keys = settings.groq_api_keys
        _key_manager.initialize(keys)
        _key_manager_initialized = True
    return _key_manager


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


# ── LLM builders ─────────────────────────────────────────────────────────────

def _build_chatgroq(
    model: str | None = None,
    max_tokens: int | None = None,
    response_format: dict | None = None,
    api_key: str | None = None,
) -> ChatGroq:
    model = model or settings.groq_model
    max_tokens = max_tokens or 2048
    api_key = api_key or settings.groq_api_key
    logger.debug(
        "groq_request",
        extra={
            "model": model,
            "response_format": response_format,
            "max_tokens": max_tokens,
            "temperature": 0.1,
            "api_key_suffix": api_key[-6:] if api_key else "None",
        },
    )
    kwargs: dict[str, Any] = {
        "model": model,
        "temperature": 0.1,
        "max_tokens": max_tokens,
        "api_key": api_key,
        "timeout": settings.groq_timeout,
        "max_retries": 0,  # We handle retries ourselves in _invoke_with_key_rotation
    }
    if response_format is not None:
        kwargs["model_kwargs"] = {"response_format": response_format}
    return ChatGroq(**kwargs)


@lru_cache(maxsize=128)
def get_llm(
    model: str | None = None, max_tokens: int | None = None, api_key: str | None = None
) -> ChatGroq:
    """Return a cached ChatGroq instance without JSON mode."""
    return _build_chatgroq(model, max_tokens, None, api_key)


@lru_cache(maxsize=128)
def get_llm_json(
    model: str | None = None, max_tokens: int | None = None, api_key: str | None = None
) -> ChatGroq:
    """Return a cached ChatGroq instance with JSON mode."""
    return _build_chatgroq(model, max_tokens, {"type": "json_object"}, api_key)


# ── Rotated Invocation Handler ───────────────────────────────────────────────

async def _invoke_with_key_rotation(
    msgs: list[BaseMessage],
    model_name: str,
    max_tokens: int | None = None,
    response_format: dict | None = None,
) -> Any:
    """
    Invoke Groq using a key from the rotated API key pool.
    If a 429 rate limit is hit, the key is put in cooldown and we IMMEDIATELY
    retry the call with the next healthy API key, avoiding unnecessary sleep delays.
    """
    key_manager = _get_key_manager()
    max_attempts = settings.groq_max_retries + 1

    for attempt in range(max_attempts):
        key, recovery_time = await key_manager.get_key_info()
        now = time.time()

        # If the selected key is in cooldown (which means all keys are), sleep until it's ready.
        if recovery_time > now:
            wait_duration = recovery_time - now
            logger.warning(
                "all_groq_keys_cooldown",
                extra={
                    "wait_time": round(wait_duration, 2),
                    "attempt": attempt + 1,
                }
            )
            await asyncio.sleep(wait_duration)

        # Build ChatGroq instance with this key
        if response_format is not None:
            llm = get_llm_json(model_name, max_tokens, key)
        else:
            llm = get_llm(model_name, max_tokens, key)

        try:
            return await llm.ainvoke(msgs)
        except Exception as exc:
            err_str = str(exc).lower()
            is_rate_limit = any(
                phrase in err_str
                for phrase in ("429", "rate limit", "too many requests", "rate_limit")
            )
            if is_rate_limit:
                # Mark the current key as rate-limited
                await key_manager.mark_cooldown(key, duration=45.0)

                # If we have attempts remaining, loop immediately to try the next key
                if attempt < max_attempts - 1:
                    logger.warning(
                        "groq_rate_limit_rotation",
                        extra={
                            "failed_key_suffix": key[-6:],
                            "attempt": attempt + 1,
                            "model": model_name,
                        }
                    )
                    # Tiny settling pause before switching keys
                    await asyncio.sleep(0.1)
                    continue
            raise

    # Fallback to try one last time
    key, _ = await key_manager.get_key_info()
    if response_format is not None:
        llm = get_llm_json(model_name, max_tokens, key)
    else:
        llm = get_llm(model_name, max_tokens, key)
    return await llm.ainvoke(msgs)


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
                        response = await _invoke_with_key_rotation(
                            messages,
                            model_for_log,
                            max_tokens,
                            {"type": "json_object"}
                        )
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

            response = await _invoke_with_key_rotation(
                modified_messages,
                model_for_log,
                max_tokens,
                None
            )

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
                    response = await _invoke_with_key_rotation(
                        repair_messages,
                        model_for_log,
                        max_tokens,
                        None
                    )

    logger.info(
        "groq_call_success",
        extra={"mode": "text", "model": model_for_log, "lane": lane},
    )
    return response
