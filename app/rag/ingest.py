"""
Document ingestion pipeline.

Loads PDF and TXT files from the data directory, chunks them, generates
embeddings, upserts vectors to Pinecone, and builds BM25+ indexes.

Usage (one-off):
    python -m app.rag.ingest

Or via API:
    POST /upload   (multipart form — uploads a single file to a domain)

Domain data directory mapping
──────────────────────────────
  data/Ayurveda/  → namespace "ayurveda"
  data/Homeopathy/ → namespace "homeopathy"
  data/Sidha/     → namespace "siddha"
  data/Unaini/    → namespace "unani"
  data/Yoga/      → namespace "yoga"
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from typing import BinaryIO

# pyrefly: ignore [missing-import]
import fitz  # PyMuPDF

from app.config import settings
from app.rag import bm25_store
from app.rag.chunking import chunk_text
from app.rag.pinecone_client import upsert_records_pinecone
from app.schemas.rag import DocumentChunk, IngestResult
from app.utils.helpers import clean_text
from app.utils.logger import get_logger

log = get_logger(__name__)

# Folder name → canonical domain name
DOMAIN_MAP: dict[str, str] = {
    "Ayurveda": "ayurveda",
    "Ayurveda ": "ayurveda",   # trailing space variant
    "Homeopathy": "homeopathy",
    "Homeopathy ": "homeopathy",
    "Sidha": "siddha",
    "Unaini": "unani",
    "Yoga": "yoga",
}


# ── Low-level file loaders ────────────────────────────────────────────────────

def _load_pdf_pages(path: Path) -> list[tuple[int, str]]:
    """
    Extract text from a PDF page-by-page using PyMuPDF.

    Returns a list of (page_number, text) tuples.
    Pages with fewer than 50 characters of text are skipped (likely images).
    """
    results: list[tuple[int, str]] = []
    try:
        doc = fitz.open(str(path))
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            text = clean_text(text)
            if len(text.strip()) >= 5:
                results.append((page_num + 1, text))
        doc.close()
    except Exception as exc:
        log.error("pdf_load_error", path=str(path), error=str(exc))
    return results


def _load_txt(path: Path) -> list[tuple[int, str]]:
    """Load a plain-text file as a single 'page'."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        text = clean_text(text)
        if text:
            return [(1, text)]
    except Exception as exc:
        log.error("txt_load_error", path=str(path), error=str(exc))
    return []


def _chunk_id(domain: str, source_file: str, page: int, idx: int) -> str:
    """Generate a deterministic, URL-safe chunk identifier."""
    raw = f"{domain}_{source_file}_{page}_{idx}"
    return hashlib.md5(raw.encode()).hexdigest()


# ── Core ingest function ──────────────────────────────────────────────────────

def ingest_domain(domain_folder: Path, domain: str) -> IngestResult:
    """
    Ingest all PDF and TXT files under *domain_folder* into the given *domain*.

    Steps per file:
      1. Extract text (PyMuPDF for PDF, plain read for TXT)
      2. Chunk with sliding-window sentence-aware chunker
      3. Batch-embed with BAAI/bge-small-en-v1.5
      4. Upsert to Pinecone (namespace=domain)
      5. Accumulate chunks for BM25 index
    After all files: save BM25+ index to disk.
    """
    result = IngestResult(
        domain=domain,
        files_processed=0,
        chunks_created=0,
        vectors_upserted=0,
        bm25_index_saved=False,
    )

    all_chunks_for_bm25: list[dict] = []
    supported_exts = {".pdf", ".txt"}

    files = sorted(
        f for f in domain_folder.iterdir()
        if f.suffix.lower() in supported_exts and not f.name.startswith(".")
    )

    log.info("ingest_domain_start", domain=domain, num_files=len(files))

    for file_path in files:
        log.info("ingest_file_start", file=file_path.name)

        # Load pages
        if file_path.suffix.lower() == ".pdf":
            pages = _load_pdf_pages(file_path)
        else:
            pages = _load_txt(file_path)

        if not pages:
            log.warning("ingest_file_empty", file=file_path.name)
            continue

        file_chunks: list[DocumentChunk] = []
        for page_num, page_text in pages:
            sub_chunks = chunk_text(page_text)
            for idx, chunk_text_str in enumerate(sub_chunks):
                if not chunk_text_str.strip():
                    continue
                file_chunks.append(
                    DocumentChunk(
                        chunk_id=_chunk_id(domain, file_path.stem, page_num, idx),
                        text=chunk_text_str,
                        domain=domain,
                        source_file=file_path.name,
                        page=page_num,
                        chunk_index=idx,
                    )
                )

        if not file_chunks:
            log.warning("ingest_file_no_chunks", file=file_path.name)
            continue

        log.info("ingest_file_chunks", file=file_path.name, chunks=len(file_chunks))

        # Build Pinecone records for integrated embeddings
        records: list[dict] = []
        for chunk in file_chunks:
            records.append(
                {
                    "_id": chunk.chunk_id,
                    "text": chunk.text,
                    "domain": chunk.domain,
                    "source_file": chunk.source_file,
                    "page": chunk.page,
                    "chunk_index": chunk.chunk_index,
                }
            )

        # Upsert
        try:
            upserted = upsert_records_pinecone(records, namespace=domain)
            result.vectors_upserted += upserted
        except Exception as exc:
            log.error("ingest_upsert_error", file=file_path.name, error=str(exc))
            result.errors.append(f"{file_path.name}: upsert failed — {exc}")
            continue

        # Accumulate for BM25
        for chunk in file_chunks:
            all_chunks_for_bm25.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "text": chunk.text,
                    "domain": chunk.domain,
                    "source_file": chunk.source_file,
                    "page": chunk.page,
                }
            )

        result.files_processed += 1
        result.chunks_created += len(file_chunks)
        log.info(
            "ingest_file_done",
            file=file_path.name,
            chunks=len(file_chunks),
            vectors=upserted,
        )

    # Build and persist BM25 index for the entire domain
    if all_chunks_for_bm25:
        try:
            bm25_store.build_and_save(domain, all_chunks_for_bm25)
            result.bm25_index_saved = True
        except Exception as exc:
            log.error("ingest_bm25_error", domain=domain, error=str(exc))
            result.errors.append(f"BM25 index build failed: {exc}")

    log.info(
        "ingest_domain_done",
        domain=domain,
        files=result.files_processed,
        chunks=result.chunks_created,
        vectors=result.vectors_upserted,
    )
    return result


def ingest_single_file(
    file_content: bytes,
    filename: str,
    domain: str,
) -> IngestResult:
    """
    Ingest a single uploaded file (from POST /upload).
    Writes to a temp file, runs the standard pipeline, then cleans up.
    """
    suffix = Path(filename).suffix.lower()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file_content)
        tmp_path = Path(tmp.name)

    try:
        result = IngestResult(
            domain=domain,
            files_processed=0,
            chunks_created=0,
            vectors_upserted=0,
            bm25_index_saved=False,
        )

        if suffix == ".pdf":
            pages = _load_pdf_pages(tmp_path)
        elif suffix == ".txt":
            pages = _load_txt(tmp_path)
        else:
            result.errors.append(f"Unsupported file type: {suffix}")
            return result

        file_chunks: list[DocumentChunk] = []
        for page_num, page_text in pages:
            for idx, ct in enumerate(chunk_text(page_text)):
                if ct.strip():
                    file_chunks.append(
                        DocumentChunk(
                            chunk_id=_chunk_id(domain, Path(filename).stem, page_num, idx),
                            text=ct,
                            domain=domain,
                            source_file=filename,
                            page=page_num,
                            chunk_index=idx,
                        )
                    )

        if not file_chunks:
            result.errors.append("No text could be extracted from the file.")
            return result

        records = [
            {
                "_id": c.chunk_id,
                "text": c.text,
                "domain": c.domain,
                "source_file": c.source_file,
                "page": c.page,
                "chunk_index": c.chunk_index,
            }
            for c in file_chunks
        ]

        result.vectors_upserted = upsert_records_pinecone(records, namespace=domain)
        result.files_processed = 1
        result.chunks_created = len(file_chunks)

        # Append to existing BM25 index or build new one
        existing_chunks: list[dict] = []
        if bm25_store.index_exists(domain):
            import json
            from app.rag.bm25_store import _corpus_path
            with open(_corpus_path(domain), "r", encoding="utf-8") as f:
                existing_chunks = json.load(f)

        new_chunks_meta = [
            {
                "chunk_id": c.chunk_id,
                "text": c.text,
                "domain": c.domain,
                "source_file": c.source_file,
                "page": c.page,
            }
            for c in file_chunks
        ]
        bm25_store.build_and_save(domain, existing_chunks + new_chunks_meta)
        result.bm25_index_saved = True

        return result
    finally:
        tmp_path.unlink(missing_ok=True)


# ── CLI entry point ───────────────────────────────────────────────────────────

def run_full_ingest() -> None:
    """Ingest all documents from all domain folders."""
    data_root = Path(settings.data_dir)
    if not data_root.exists():
        log.error("data_dir_not_found", path=str(data_root))
        return

    for folder in sorted(data_root.iterdir()):
        if not folder.is_dir():
            continue

        name_lower = folder.name.strip().lower()
        if "ayurveda" in name_lower:
            domain = "ayurveda"
        elif "homeopathy" in name_lower:
            domain = "homeopathy"
        elif "sidha" in name_lower or "siddha" in name_lower:
            domain = "siddha"
        elif "unaini" in name_lower or "unani" in name_lower:
            domain = "unani"
        elif "yoga" in name_lower:
            domain = "yoga"
        else:
            log.warning("unknown_folder_skipped", folder=folder.name)
            continue

        result = ingest_domain(folder, domain)
        log.info("ingest_summary", **result.model_dump())


if __name__ == "__main__":
    from app.utils.logger import configure_logging
    configure_logging()
    run_full_ingest()
