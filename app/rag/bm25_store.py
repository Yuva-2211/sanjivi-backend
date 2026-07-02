"""
BM25 sparse index store.

Uses the `bm25s` library which implements BM25+ (a BM2.5-family variant
with improved term-frequency and document-length normalisation).

One index is maintained per AYUSH domain.  Indexes are serialised to
disk under `BM25_INDEX_DIR/{domain}/` and loaded lazily on first access.

Alongside the BM25 retriever itself we persist a `corpus.json` that
stores the full chunk metadata (text, source_file, page, chunk_id) so
we can reconstruct `RetrievedChunk` objects from the integer matches
returned by BM25.
"""

from __future__ import annotations

import asyncio
import json
import os
import pickle
from pathlib import Path
from typing import Optional

# pyrefly: ignore [missing-import]
import bm25s

from app.config import settings
from app.schemas.rag import RetrievedChunk
from app.utils.logger import get_logger

log = get_logger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────

def _index_dir(domain: str) -> Path:
    base = Path(settings.bm25_index_dir)
    d = base / domain
    d.mkdir(parents=True, exist_ok=True)
    return d


def _corpus_path(domain: str) -> Path:
    return _index_dir(domain) / "corpus.json"


def _retriever_path(domain: str) -> Path:
    return _index_dir(domain) / "retriever.pkl"


# ── In-process cache ──────────────────────────────────────────────────────────

_cache: dict[str, tuple[bm25s.BM25, list[dict]]] = {}


# ── Public API ────────────────────────────────────────────────────────────────

def build_and_save(domain: str, chunks: list[dict]) -> None:
    """
    Build a BM25+ index from *chunks* and persist it to disk.

    Each chunk dict must contain: chunk_id, text, source_file, page, domain.
    """
    if not chunks:
        log.warning("bm25_build_skipped_empty", domain=domain)
        return

    corpus_texts = [c["text"] for c in chunks]

    # Tokenise — bm25s uses its own whitespace tokeniser by default
    tokenised = bm25s.tokenize(corpus_texts, stopwords="en")

    # BM25+ variant (method="bm25+") improves recall on long documents
    retriever = bm25s.BM25(method="bm25+")
    retriever.index(tokenised)

    # Save retriever
    retriever.save(str(_index_dir(domain)))

    # Save corpus metadata (text + provenance)
    corpus_meta = [
        {
            "chunk_id": c["chunk_id"],
            "text": c["text"],
            "source_file": c["source_file"],
            "page": c.get("page"),
            "domain": c["domain"],
        }
        for c in chunks
    ]
    with open(_corpus_path(domain), "w", encoding="utf-8") as f:
        json.dump(corpus_meta, f, ensure_ascii=False)

    # Update in-memory cache
    _cache[domain] = (retriever, corpus_meta)

    log.info(
        "bm25_index_saved",
        domain=domain,
        num_docs=len(corpus_texts),
        path=str(_index_dir(domain)),
    )


def _load(domain: str) -> tuple[bm25s.BM25, list[dict]] | None:
    """Load index from disk into the in-process cache."""
    corp_path = _corpus_path(domain)

    if not corp_path.exists():
        log.warning("bm25_index_not_found", domain=domain)
        return None

    try:
        retriever = bm25s.BM25.load(str(_index_dir(domain)))
    except Exception as exc:
        log.error("bm25_load_failed", domain=domain, error=str(exc))
        return None

    with open(corp_path, "r", encoding="utf-8") as f:
        corpus_meta = json.load(f)

    _cache[domain] = (retriever, corpus_meta)
    log.info("bm25_index_loaded", domain=domain, num_docs=len(corpus_meta))
    return retriever, corpus_meta


def search(
    domain: str,
    query: str,
    top_k: int | None = None,
) -> list[RetrievedChunk]:
    """
    Search the BM25 index for *domain* and return ranked chunks.

    Returns an empty list if no index exists for the domain yet.
    """
    top_k = top_k or settings.top_k_bm25

    # Lazy-load from disk if not already in cache
    if domain not in _cache:
        if not index_exists(domain):
            if domain != "homeopathy":
                log.warning("bm25_index_missing_fallback_dense", domain=domain)
            return []
        result = _load(domain)
        if result is None:
            if domain != "homeopathy":
                log.warning("bm25_load_failed_fallback_dense", domain=domain)
            return []

    retriever, corpus_meta = _cache[domain]

    query_tokens = bm25s.tokenize([query], stopwords="en")
    raw_results, scores = retriever.retrieve(query_tokens, k=min(top_k, len(corpus_meta)))

    retrieved: list[RetrievedChunk] = []
    for rank, (idx, score) in enumerate(zip(raw_results[0], scores[0])):
        meta = corpus_meta[int(idx)]
        retrieved.append(
            RetrievedChunk(
                chunk_id=meta["chunk_id"],
                text=meta["text"],
                domain=meta["domain"],
                source_file=meta["source_file"],
                page=meta.get("page"),
                rrf_score=float(score),   # will be overwritten by RRF
                bm25_rank=rank,
            )
        )

    return retrieved


async def search_async(
    domain: str,
    query: str,
    top_k: int | None = None,
) -> list[RetrievedChunk]:
    """Async wrapper around `search` (offloads to thread pool)."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, search, domain, query, top_k)


def index_exists(domain: str) -> bool:
    """Return True if a persisted BM25 index exists for this domain."""
    return _corpus_path(domain).exists()
