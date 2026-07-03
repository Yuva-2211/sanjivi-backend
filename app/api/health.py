"""
Health and Document API Endpoints.

Provides system health checks (checking Groq and Pinecone connectivity)
and list/delete operations for reference documents.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.config import settings
from app.models.llm import get_llm, get_openrouter_llm
from app.rag import bm25_store
from app.rag.bm25_store import _corpus_path, build_and_save
from app.rag.pinecone_client import get_index, list_namespace_stats
from app.utils.logger import get_logger

log = get_logger(__name__)

router = APIRouter()


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Check backend health",
    description="Verifies connectivity to Groq, OpenRouter, and Pinecone vector database.",
)
async def health_endpoint() -> dict[str, Any]:
    """
    Verify all dependent services are responsive.
    """
    health_status = {
        "status": "healthy",
        "services": {
            "groq": "unknown",
            "openrouter": "unknown",
            "pinecone": "unknown",
        },
    }

    # 1. Test Groq
    try:
        llm = get_llm()
        await llm.ainvoke("ping json")
        health_status["services"]["groq"] = "connected"
    except Exception as exc:
        log.error("health_check_groq_failed", error=str(exc))
        health_status["services"]["groq"] = f"failed: {exc}"
        health_status["status"] = "unhealthy"

    # 2. Test OpenRouter
    try:
        llm = get_openrouter_llm(settings.ayurveda_model)
        await llm.ainvoke("ping")
        health_status["services"]["openrouter"] = "connected"
    except Exception as exc:
        log.error("health_check_openrouter_failed", error=str(exc))
        health_status["services"]["openrouter"] = f"failed: {exc}"
        health_status["status"] = "unhealthy"

    # 3. Test Pinecone
    try:
        stats = list_namespace_stats()
        health_status["services"]["pinecone"] = {
            "status": "connected",
            "namespaces": stats.get("namespaces", {}),
        }
    except Exception as exc:
        log.error("health_check_pinecone_failed", error=str(exc))
        health_status["services"]["pinecone"] = f"failed: {exc}"
        health_status["status"] = "unhealthy"

    if health_status["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status,
        )

    return health_status


@router.get(
    "/documents",
    status_code=status.HTTP_200_OK,
    summary="List all ingested documents",
    description="Scans the local BM25 corpus indexes and lists all files that have been ingested, grouped by domain.",
)
async def list_documents_endpoint() -> list[dict[str, Any]]:
    """
    List all ingested files with metadata and chunk counts.
    """
    documents = []
    valid_domains = ["ayurveda", "siddha", "unani", "homeopathy", "yoga"]

    for domain in valid_domains:
        corp_path = _corpus_path(domain)
        if not corp_path.exists():
            continue

        try:
            with open(corp_path, "r", encoding="utf-8") as f:
                corpus = json.load(f)

            # Count chunks per unique file
            file_counts: dict[str, int] = {}
            for chunk in corpus:
                fname = chunk.get("source_file", "unknown")
                file_counts[fname] = file_counts.get(fname, 0) + 1

            for fname, count in file_counts.items():
                documents.append(
                    {
                        "id": f"{domain}:{fname}",
                        "filename": fname,
                        "domain": domain,
                        "chunks": count,
                    }
                )
        except Exception as exc:
            log.error("list_documents_parse_error", domain=domain, error=str(exc))

    return documents


@router.delete(
    "/documents/{id:path}",
    status_code=status.HTTP_200_OK,
    summary="Delete an ingested document",
    description="Deletes a document from the Pinecone namespace and rebuilds the local BM25 index without its chunks. The ID format should be '{domain}:{filename}'.",
)
async def delete_document_endpoint(id: str) -> dict[str, Any]:
    """
    Delete a document and rebuild the sparse index.
    """
    if ":" not in id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document ID must be in the format '{domain}:{filename}'",
        )

    domain, filename = id.split(":", 1)
    valid_domains = {"ayurveda", "siddha", "unani", "homeopathy", "yoga"}

    if domain not in valid_domains:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid domain '{domain}'. Must be one of: {', '.join(valid_domains)}",
        )

    log.info("api_delete_document", domain=domain, filename=filename)

    # 1. Delete from Pinecone
    try:
        index = get_index()
        # Delete by metadata filter
        index.delete(
            filter={"source_file": {"$eq": filename}},
            namespace=domain,
        )
        log.info("pinecone_chunks_deleted", filename=filename, namespace=domain)
    except Exception as exc:
        log.error("delete_pinecone_error", id=id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete from vector store: {exc}",
        )

    # 2. Update local BM25 corpus and index
    corp_path = _corpus_path(domain)
    if corp_path.exists():
        try:
            with open(corp_path, "r", encoding="utf-8") as f:
                corpus = json.load(f)

            # Filter out chunks matching the deleted filename
            remaining_chunks = [
                c for c in corpus
                if c.get("source_file") != filename
            ]

            if len(remaining_chunks) < len(corpus):
                if remaining_chunks:
                    # Rebuild BM25 index with remaining chunks
                    build_and_save(domain, remaining_chunks)
                else:
                    # Clean up index files if no chunks are left
                    corp_path.unlink(missing_ok=True)
                    ret_path = bm25_store._retriever_path(domain)
                    ret_path.unlink(missing_ok=True)
                    # Clear cache entry
                    if domain in bm25_store._cache:
                        del bm25_store._cache[domain]
                    log.info("bm25_index_removed_empty", domain=domain)
            else:
                log.warning("bm25_document_not_found_in_corpus", filename=filename, domain=domain)
        except Exception as exc:
            log.error("delete_bm25_rebuild_error", id=id, error=str(exc))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to rebuild sparse index: {exc}",
            )

    return {
        "status": "success",
        "message": f"Successfully deleted '{filename}' from domain '{domain}'",
    }
