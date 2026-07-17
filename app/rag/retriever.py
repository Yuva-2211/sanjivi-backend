"""
Hybrid Retriever — combines BM25+ sparse retrieval with dense Pinecone
retrieval using Reciprocal Rank Fusion (RRF).

Pipeline per query:
  1. Dense retrieval  → Pinecone cosine search        (top_k_dense results)
  2. Sparse retrieval → BM25+ index search            (top_k_bm25 results)
  3. RRF fusion       → merge both ranked lists       (top_k_rerank candidates)
  4. Return           → top_k_final RetrievedChunk objects

Each expert agent instantiates one HybridRetriever for its own domain so
retrieval is always namespace-isolated.
"""

from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Sequence

from app.config import settings
from app.rag import bm25_store
from app.rag.pinecone_client import search_namespace
from app.schemas.rag import RetrievedChunk
from app.utils.logger import get_logger

log = get_logger(__name__)


@lru_cache(maxsize=8)
def get_hybrid_retriever(domain: str) -> "HybridRetriever":
    """Return a cached HybridRetriever instance for the given domain."""
    return HybridRetriever(domain)


# ── RRF implementation ────────────────────────────────────────────────────────

def _rrf_fusion(
    dense_chunks: list[RetrievedChunk],
    sparse_chunks: list[RetrievedChunk],
    k: int | None = None,
) -> list[RetrievedChunk]:
    """
    Reciprocal Rank Fusion.

    score(doc) = Σ  1 / (k + rank_i)

    Merges two ranked lists, de-duplicates by chunk_id, and returns all
    unique chunks sorted by descending fused score.
    """
    k = k or settings.rrf_k
    scores: dict[str, float] = {}
    meta: dict[str, RetrievedChunk] = {}

    for rank, chunk in enumerate(dense_chunks):
        cid = chunk.chunk_id
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)
        if cid not in meta:
            chunk.dense_rank = rank
            meta[cid] = chunk

    for rank, chunk in enumerate(sparse_chunks):
        cid = chunk.chunk_id
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)
        if cid not in meta:
            chunk.bm25_rank = rank
            meta[cid] = chunk
        else:
            meta[cid].bm25_rank = rank

    sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)
    for cid in sorted_ids:
        meta[cid].rrf_score = scores[cid]

    return [meta[cid] for cid in sorted_ids]


# ── Converter helpers ─────────────────────────────────────────────────────────

def _pinecone_matches_to_chunks(matches: list[dict]) -> list[RetrievedChunk]:
    """Convert raw Pinecone match dicts to RetrievedChunk objects."""
    chunks: list[RetrievedChunk] = []
    for rank, m in enumerate(matches):
        md = m.get("metadata", {})
        chunks.append(
            RetrievedChunk(
                chunk_id=m["id"],
                text=md.get("text", ""),
                domain=md.get("domain", ""),
                source_file=md.get("source_file", ""),
                page=md.get("page"),
                rrf_score=m.get("score", 0.0),
                dense_rank=rank,
            )
        )
    return chunks


# ── Main retriever ────────────────────────────────────────────────────────────

class HybridRetriever:
    """
    Domain-scoped hybrid retriever.

    Usage::

        retriever = HybridRetriever("ayurveda")
        chunks = await retriever.retrieve("joint pain and stiffness")
    """

    def __init__(self, domain: str) -> None:
        self.domain = domain

    async def retrieve(
        self,
        query: str,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        """
        Retrieve the top *top_k* chunks for *query* using hybrid RRF search.
        """
        top_k = top_k or settings.top_k_final

        log.info("retriever_start", domain=self.domain, query=query[:80])

        # Run dense and sparse retrieval concurrently
        # Dense retrieval (Pinecone) — synchronous SDK call in executor
        loop = asyncio.get_event_loop()
        dense_task = loop.run_in_executor(
            None,
            search_namespace,
            query,
            self.domain,
            settings.top_k_dense,
        )

        raw_dense, sparse_results = await asyncio.gather(
            dense_task,
            bm25_store.search_async(
                domain=self.domain,
                query=query,
                top_k=settings.top_k_bm25,
            ),
        )

        dense_results = _pinecone_matches_to_chunks(raw_dense)

        log.info(
            "retriever_results",
            domain=self.domain,
            dense=len(dense_results),
            sparse=len(sparse_results),
        )

        # RRF fusion
        fused = _rrf_fusion(dense_results, sparse_results, k=settings.rrf_k)

        # Return top-k after fusion
        final = fused[: settings.top_k_rerank]

        log.info("retriever_done", domain=self.domain, returned=len(final))
        return final[:top_k]


def build_context_string(chunks: Sequence[RetrievedChunk], max_chars: int | None = None) -> str:
    """
    Format retrieved chunks into a context block for the LLM prompt.

    Each chunk is prefixed with its source so the model can cite it.
    Total context is capped at *max_chars* to stay within token limits.
    Always includes at least one chunk if any exist.
    """
    max_chars = max_chars or settings.context_max_chars
    parts: list[str] = []
    total = 0
    for chunk in chunks:
        header = f"[Source: {chunk.source_file}, page {chunk.page}]"
        entry = f"{header}\n{chunk.text}\n"
        if total + len(entry) > max_chars and parts:
            # Already have at least one chunk — stop here
            break
        parts.append(entry)
        total += len(entry)
    return "\n---\n".join(parts)
