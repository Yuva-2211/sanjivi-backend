"""
Sanjivi AI Backend — FastAPI Main Application.

Initialises logging, configures CORS, registers router endpoints,
and handles startup and shutdown event hooks.
"""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, health, upload
from app.config import settings
from app.utils.logger import configure_logging, get_logger

# 1. Configure structured logging
configure_logging()
log = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup/shutdown actions.
    """
    log.info("sanjivi_backend_starting", model=settings.groq_model, index=settings.pinecone_index)
    
    # 1. Pre-compile the LangGraph state graph at startup
    from app.agents.orchestrator import get_graph
    get_graph()

    # 2. Warm up Pinecone Index client to cache the connection and index info
    from app.rag.pinecone_client import get_index
    try:
        get_index()
        log.info("pinecone_index_cached_at_startup")
    except Exception as exc:
        log.error("pinecone_startup_warmup_failed", error=str(exc))

    # 3. Warm up/load all BM25 sparse indexes into memory cache
    from app.rag.bm25_store import _load, index_exists
    for domain in ["ayurveda", "siddha", "unani", "homeopathy", "yoga"]:
        try:
            if index_exists(domain):
                _load(domain)
        except Exception as exc:
            log.error("bm25_startup_warmup_failed", domain=domain, error=str(exc))

    log.info("sanjivi_backend_ready")
    yield
    log.info("sanjivi_backend_shutting_down")


# 2. Instantiate FastAPI
app = FastAPI(
    title="Sanjivi AI Backend",
    description="Multi-Agent AYUSH RAG Healthcare System Backend powered by LangGraph, Groq, Pinecone, and FastAPI.",
    version="1.0.0",
    lifespan=lifespan,
)

# 3. Configure CORS (allow frontend origin)
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://sanjivi-1729labs.vercel.app",
]
if settings.frontend_url and settings.frontend_url not in origins:
    origins.append(settings.frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)


# 4. Middleware for request-response logging & timing
@app.middleware("http")
async def log_requests(request: Request, call_next: Any) -> Any:
    request_id = str(uuid.uuid4())
    start_time = time.time()
    path = request.url.path
    method = request.method
    log.info("http_request_start", request_id=request_id, path=path, method=method)

    try:
        response = await call_next(request)
        duration = time.time() - start_time
        log.info(
            "http_request_done",
            request_id=request_id,
            path=path,
            method=method,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2),
        )
        return response
    except Exception as exc:
        duration = time.time() - start_time
        log.error(
            "http_request_failed",
            request_id=request_id,
            path=path,
            method=method,
            error=str(exc),
            duration_ms=round(duration * 1000, 2),
        )
        raise exc


# 5. Register Routers (direct mappings to meet user's API specification)
app.include_router(chat.router, tags=["Chat"])
app.include_router(upload.router, tags=["Upload"])
app.include_router(health.router, tags=["System & Documents"])
