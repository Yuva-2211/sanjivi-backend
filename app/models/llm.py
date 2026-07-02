"""
LLM provider — Groq via LangChain.

This module provides cached ChatGroq instances with a JSON-mode
fallback strategy to avoid 400 Bad Request (json_validate_failed)
errors on models that do not support structured JSON output.
"""

from __future__ import annotations

import logging
import asyncio
import random
from functools import lru_cache
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq

from app.config import settings
from app.utils.helpers import parse_json_response


logger = logging.getLogger(__name__)

# Models known NOT to support response_format={"type": "json_object"} via Groq.
# Listing them here avoids a wasted round-trip (try JSON → get 400 → retry text).
_JSON_MODE_UNSUPPORTED: set[str] = {
    "openai/gpt-oss-120b",
}

_json_mode_supported: dict[str, bool] = {
    m: False for m in _JSON_MODE_UNSUPPORTED
}

# Allow all 5 domain experts + consensus + reviewer to run concurrently.
_groq_semaphore = asyncio.Semaphore(8)


async def _invoke_with_retry(llm: ChatGroq, msgs: list[BaseMessage], model_name: str) -> Any:
    """Invoke Groq with exponential backoff and jitter on 429 (Rate Limit) errors."""
    for attempt in range(5):
        try:
            return await llm.ainvoke(msgs)
        except Exception as exc:
            err_str = str(exc).lower()
            is_rate_limit = any(
                phrase in err_str
                for phrase in ("429", "rate limit", "too many requests", "rate_limit")
            )
            if is_rate_limit:
                # 2, 4, 8, 16, 32 seconds backoff with some random jitter
                wait_time = (2 ** (attempt + 1)) + random.uniform(0.5, 1.5)
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
    # Final try
    return await llm.ainvoke(msgs)


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
        "max_retries": settings.groq_max_retries,
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


async def call_llm(
    messages: list[BaseMessage],
    model: str | None = None,
    max_tokens: int | None = None,
    force_json: bool = True,
) -> Any:
    """
    Invoke Groq with JSON mode first, falling back to plain text on failure.

    This prevents the pipeline from crashing when the selected model
    does not support response_format={"type": "json_object"}.
    """
    model_for_log = model or settings.groq_model
    max_tokens_for_log = max_tokens or 2048
    logger.debug(
        "groq_call",
        extra={
            "model": model_for_log,
            "max_tokens": max_tokens_for_log,
            "temperature": 0.1,
            "messages": str(messages)[:2000],
        },
    )

    async with _groq_semaphore:
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
                        extra={
                            "mode": "json",
                            "model": model_for_log,
                        },
                    )
                    return response
                except Exception as exc:
                    reason = str(exc).lower()
                    if any(keyword in reason for keyword in ("response_format", "json", "validate", "bad request", "unsupported", "invalid")):
                        _json_mode_supported[model_for_log] = False
                    logger.info(
                        "groq_json_mode_disabled",
                        extra={
                            "model": model_for_log,
                            "error": str(exc)[:300],
                        },
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
        extra={
            "mode": "text",
            "model": model_for_log,
        },
    )
    return response
