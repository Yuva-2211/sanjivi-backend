"""
Pinecone client — initialises the index (creating it if absent) and
provides per-domain namespace helpers.
"""

from __future__ import annotations

import time
from functools import lru_cache

from pinecone import Pinecone, ServerlessSpec

from app.config import settings
from app.utils.logger import get_logger

log = get_logger(__name__)

# Mapping from domain name to Pinecone namespace
DOMAIN_NAMESPACES: dict[str, str] = {
    "ayurveda": "ayurveda",
    "siddha": "siddha",
    "unani": "unani",
    "homeopathy": "homeopathy",
    "yoga": "yoga",
}


@lru_cache(maxsize=1)
def get_pinecone_client() -> Pinecone:
    """Return a cached Pinecone client instance."""
    return Pinecone(api_key=settings.pinecone_api_key)


_index = None


def get_index():
    """
    Return the Pinecone Index object. Cached to prevent redundant list_indexes calls.
    """
    global _index
    if _index is None:
        pc = get_pinecone_client()
        existing = [idx.name for idx in pc.list_indexes()]

        if settings.pinecone_index not in existing:
            log.error("pinecone_index_not_found", index=settings.pinecone_index)
            raise RuntimeError(
                f"Pinecone index '{settings.pinecone_index}' does not exist. "
                "Please create it in your Pinecone Console with integrated embeddings "
                "(model: llama-text-embed-v2, dimension: 1024, metric: cosine, text field map: text)."
            )
        _index = pc.Index(settings.pinecone_index)

    return _index


def upsert_records_pinecone(
    records: list[dict],
    namespace: str,
    batch_size: int = 90,
) -> int:
    """
    Upsert a list of document record dicts using Pinecone Inference API.
    Retries automatically on 429 rate-limit errors with exponential backoff.
    """
    pc = get_pinecone_client()
    index = get_index()
    total = 0
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        texts = [doc["text"] for doc in batch]

        # Embed with retry on 429
        for attempt in range(5):
            try:
                embed_resp = pc.inference.embed(
                    model="llama-text-embed-v2",
                    inputs=texts,
                    parameters={"input_type": "passage", "truncate": "END"}
                )
                break
            except Exception as exc:
                if "429" in str(exc) or "rate" in str(exc).lower():
                    wait = 2 ** attempt * 5  # 5, 10, 20, 40, 80 seconds
                    log.warning("pinecone_embed_ratelimit", attempt=attempt, wait=wait)
                    time.sleep(wait)
                else:
                    raise
        else:
            raise RuntimeError("Max retries exceeded on Pinecone inference embed")

        vectors = []
        for j, doc in enumerate(batch):
            vectors.append({
                "id": doc.get("id") or doc.get("_id"),
                "values": embed_resp.data[j].values,
                "metadata": {
                    "text": doc.get("text", ""),
                    "domain": doc.get("domain", ""),
                    "source_file": doc.get("source_file", ""),
                    "page": doc.get("page"),
                    "chunk_index": doc.get("chunk_index", 0)
                }
            })

        # Upsert with retry on 429
        for attempt in range(5):
            try:
                index.upsert(vectors=vectors, namespace=namespace)
                break
            except Exception as exc:
                if "429" in str(exc) or "rate" in str(exc).lower():
                    wait = 2 ** attempt * 5
                    log.warning("pinecone_upsert_ratelimit", attempt=attempt, wait=wait)
                    time.sleep(wait)
                else:
                    raise
        else:
            raise RuntimeError("Max retries exceeded on Pinecone upsert")

        total += len(batch)
        log.info("pinecone_records_upserted", namespace=namespace, count=len(batch), total=total)
    return total


def search_namespace(
    query: str,
    namespace: str,
    top_k: int = 20,
) -> list[dict]:
    """
    Query Pinecone using Inference API (client-side managed server embedding).
    """
    pc = get_pinecone_client()
    index = get_index()
    
    embed_resp = pc.inference.embed(
        model="llama-text-embed-v2",
        inputs=[query],
        parameters={"input_type": "query", "truncate": "END"}
    )
    query_vector = embed_resp.data[0].values
    
    results = index.query(
        namespace=namespace,
        vector=query_vector,
        top_k=top_k,
        include_metadata=True
    )
    
    matches = []
    for match in getattr(results, "matches", []):
        metadata = match.metadata or {}
        matches.append({
            "id": match.id,
            "score": getattr(match, "score", 0.0),
            "metadata": {
                "text": metadata.get("text", ""),
                "domain": metadata.get("domain", ""),
                "source_file": metadata.get("source_file", ""),
                "page": metadata.get("page"),
                "chunk_index": metadata.get("chunk_index", 0)
            }
        })
    return matches


def list_namespace_stats() -> dict:
    """Return index statistics grouped by namespace."""
    index = get_index()
    stats = index.describe_index_stats()
    return {
        "total_vectors": stats.total_vector_count,
        "namespaces": {
            ns: info.vector_count
            for ns, info in stats.namespaces.items()
        },
    }


def delete_namespace(namespace: str) -> None:
    """Delete all vectors in a namespace (used by DELETE /documents)."""
    index = get_index()
    index.delete(delete_all=True, namespace=namespace)
    log.info("pinecone_namespace_deleted", namespace=namespace)
