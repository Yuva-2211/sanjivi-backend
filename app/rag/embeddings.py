"""
Embeddings — wraps sentence-transformers BAAI/bge-small-en-v1.5.

The model is loaded once and reused across all agents.
Heavy encode() calls are offloaded to a thread-pool executor so they
don't block the async event loop.
"""

from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Sequence

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.utils.logger import get_logger

log = get_logger(__name__)


@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    """Load and cache the embedding model (runs once on first call)."""
    log.info("embedding_model_loading", model=settings.embedding_model)
    model = SentenceTransformer(settings.embedding_model)
    log.info("embedding_model_loaded", model=settings.embedding_model)
    return model


def embed_texts_sync(texts: Sequence[str], batch_size: int = 64) -> list[list[float]]:
    """
    Synchronous embedding — use inside thread-pool or during ingest.

    Returns a list of float vectors (one per input text).
    """
    model = _load_model()
    # bge models work best with this prefix for retrieval
    prefixed = [f"Represent this sentence for searching relevant passages: {t}" for t in texts]
    embeddings: np.ndarray = model.encode(
        prefixed,
        batch_size=batch_size,
        show_progress_bar=False,
        normalize_embeddings=True,
    )
    return embeddings.tolist()


async def embed_texts(texts: Sequence[str], batch_size: int = 64) -> list[list[float]]:
    """
    Async-safe embedding — offloads blocking encode() to a thread pool.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, embed_texts_sync, texts, batch_size)


async def embed_query(query: str) -> list[float]:
    """
    Embed a single query string.

    Uses the query-specific prefix recommended for bge models.
    """
    model = _load_model()
    loop = asyncio.get_event_loop()
    prefixed = f"Represent this sentence for searching relevant passages: {query}"
    result: np.ndarray = await loop.run_in_executor(
        None,
        lambda: model.encode(
            [prefixed],
            normalize_embeddings=True,
        ),
    )
    return result[0].tolist()
