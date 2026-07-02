"""
Chat API Endpoint.

Handles receiving user health queries, running the LangGraph orchestrator,
and returning the structured AYUSH diagnosis and recommendations response.
"""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.agents.orchestrator import run_sanjivi, stream_sanjivi
from app.schemas.chat import ChatRequest, ChatResponse, ConsensusResponse, ReviewerResponse
from app.utils.logger import get_logger

log = get_logger(__name__)

router = APIRouter()


def _is_rate_limit_error(exc: Exception) -> bool:
    """Return True when an upstream LLM provider rejected the request for quota."""
    error_text = str(exc).lower()
    return (
        "429" in error_text
        or "rate limit" in error_text
        or "rate_limit_exceeded" in error_text
        or "retryerror" in error_text
    )


def _rate_limit_response() -> ChatResponse:
    message = (
        "The Sanjivi AI backend is running, but the Groq LLM quota is temporarily exhausted. "
        "Please try again after the provider reset window, or switch to a Groq key/model with available quota."
    )
    return ChatResponse(
        emergency=False,
        patient_summary=message,
        consensus=ConsensusResponse(
            unified_recommendation=message,
            common_themes=["Backend reachable", "LLM provider quota exhausted"],
            conflicts_detected=[],
            ranked_advice=[
                "Wait for the Groq quota reset window.",
                "Use a Groq API key or model with available token quota.",
                "Retry the same question after quota is available.",
            ],
        ),
        reviewer=ReviewerResponse(
            validated=False,
            warnings=["Groq returned a rate-limit response, so no medical recommendation was generated."],
            final_answer=message,
            patient_summary=message,
        ),
    )


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit a patient health query",
    description="Processes user symptom description, runs emergency check, runs AYUSH expert agents, and compiles a consensus recommendation.",
)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Ingest user message, run the LangGraph orchestrator, and return
    the full multi-agent synthesis response.
    """
    request_id = str(uuid.uuid4())
    log.info("api_chat_request_received", request_id=request_id, query=request.message[:80])

    try:
        history_list = [{"role": h.role, "content": h.content} for h in request.history]
        response = await run_sanjivi(
            query=request.message,
            selected_system=request.selected_system,
            lat=request.lat,
            lng=request.lng,
            history=history_list,
        )
        log.info("api_chat_request_success", emergency=response.emergency)
        return response
    except ValueError as exc:
        log.warning("api_chat_request_invalid", request_id=request_id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        log.error("api_chat_request_error", request_id=request_id, error=str(exc))
        if _is_rate_limit_error(exc):
            return _rate_limit_response()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your request: {exc}",
        )


@router.post(
    "/chat/stream",
    summary="Submit a patient health query with SSE streaming",
    description="Processes user symptom description and streams intermediate agent completions as they occur.",
)
async def chat_stream_endpoint(request: ChatRequest) -> StreamingResponse:
    request_id = str(uuid.uuid4())
    log.info("api_chat_stream_request_received", request_id=request_id, query=request.message[:80])

    history_list = [{"role": h.role, "content": h.content} for h in request.history]

    async def event_generator():
        try:
            async for event in stream_sanjivi(
                query=request.message,
                selected_system=request.selected_system,
                lat=request.lat,
                lng=request.lng,
                history=history_list,
            ):
                # Format update as Server-Sent Event (SSE)
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as exc:
            log.error("api_chat_stream_error", request_id=request_id, error=str(exc))
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
