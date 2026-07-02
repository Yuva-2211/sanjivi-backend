"""
Upload API Endpoint.

Allows uploading a PDF or TXT document to a specific AYUSH domain namespace
at runtime to expand the RAG system's knowledge base.
"""

from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.rag.ingest import DOMAIN_MAP, ingest_single_file
from app.schemas.rag import IngestResult
from app.utils.logger import get_logger

log = get_logger(__name__)

router = APIRouter()


@router.post(
    "/upload",
    response_model=IngestResult,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a reference document for RAG",
    description="Uploads a PDF or TXT reference text to a specific domain (ayurveda, siddha, unani, homeopathy, yoga) and updates both Pinecone and the local BM25 index.",
)
async def upload_endpoint(
    file: UploadFile = File(..., description="The PDF or TXT file to ingest"),
    domain: str = Form(..., description="The target domain namespace (ayurveda, siddha, unani, homeopathy, yoga)"),
) -> IngestResult:
    """
    Ingest an uploaded document into the RAG vector store and BM25 index.
    """
    normalized_domain = domain.strip().lower()

    # Normalize domain using the DOMAIN_MAP keys or standard names
    valid_domains = {"ayurveda", "siddha", "unani", "homeopathy", "yoga"}
    if normalized_domain not in valid_domains:
        # Check if it matches one of the DOMAIN_MAP folder names
        found = False
        for k, v in DOMAIN_MAP.items():
            if normalized_domain == k.lower():
                normalized_domain = v
                found = True
                break
        if not found:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid domain '{domain}'. Must be one of: {', '.join(valid_domains)}",
            )

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename.",
        )

    suffix = file.filename.split(".")[-1].lower()
    if suffix not in {"pdf", "txt"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '.{suffix}'. Only PDF and TXT files are accepted.",
        )

    log.info("api_upload_request", filename=file.filename, domain=normalized_domain)

    try:
        content = await file.read()
        result = ingest_single_file(
            file_content=content,
            filename=file.filename,
            domain=normalized_domain,
        )
        if result.errors:
            log.warning("api_upload_completed_with_errors", filename=file.filename, errors=result.errors)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Ingestion completed with errors: {'; '.join(result.errors)}",
            )
        log.info("api_upload_success", filename=file.filename, chunks=result.chunks_created)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        log.error("api_upload_error", filename=file.filename, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest file: {exc}",
        )
