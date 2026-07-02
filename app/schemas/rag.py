"""
Pydantic schemas for the RAG pipeline — documents, chunks, and
ingest progress tracking.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """A single text chunk ready for embedding and upsert."""
    chunk_id: str = Field(..., description="Unique identifier: {domain}_{file_stem}_{page}_{idx}")
    text: str
    domain: str = Field(..., description="ayurveda | siddha | unani | homeopathy | yoga")
    source_file: str
    page: Optional[int] = None
    chunk_index: int = 0


class RetrievedChunk(BaseModel):
    """A chunk returned by the hybrid retriever, with its RRF score."""
    chunk_id: str
    text: str
    domain: str
    source_file: str
    page: Optional[int] = None
    rrf_score: float = 0.0
    dense_rank: Optional[int] = None
    bm25_rank: Optional[int] = None


class IngestResult(BaseModel):
    """Summary returned after ingesting a batch of documents."""
    domain: str
    files_processed: int
    chunks_created: int
    vectors_upserted: int
    bm25_index_saved: bool
    errors: list[str] = Field(default_factory=list)
