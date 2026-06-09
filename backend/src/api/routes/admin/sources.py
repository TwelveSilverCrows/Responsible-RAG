"""
routes/admin/sources.py — Admin source management
====================================================
Endpoints:
    GET    /api/v1/admin/sources           — List all sources
    GET    /api/v1/admin/sources/{id}      — Get source details
    POST   /api/v1/admin/sources           — Create source (metadata)
    PUT    /api/v1/admin/sources/{id}      — Update source metadata
    DELETE /api/v1/admin/sources/{id}      — Delete source
    POST   /api/v1/admin/sources/upload    — Upload file + ingest
    POST   /api/v1/admin/sources/url       — Ingest from URL

Admin-only (all endpoints require admin role).
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from src.api.schemas.source import (
    SourceResponse,
    SourceListResponse,
    SourceCreateRequest,
    SourceUpdateRequest,
    UploadResponse,
)
from src.api.middleware import require_admin
from src.api.db.models import User

router = APIRouter()


@router.get("", response_model=SourceListResponse)
async def list_sources(
    page: int = 1,
    limit: int = 20,
    status: str | None = None,
    admin: User = Depends(require_admin),
):
    """
    List all knowledge-base sources with optional status filter.

    Admin-only.
    """
    # TODO: Implement
    # service = SourceService()
    # sources, total = await service.list_sources(page=page, limit=limit, status=status)
    # return SourceListResponse(sources=[...], total=total, page=page, limit=limit)
    return SourceListResponse(sources=[], total=0, page=page, limit=limit)


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: str,
    admin: User = Depends(require_admin),
):
    """
    Get detailed metadata for a single source.

    Raises 404 if the source is not found.
    """
    # TODO: Implement
    raise HTTPException(status_code=404, detail="Source not found")


@router.post("", response_model=SourceResponse, status_code=201)
async def create_source(
    body: SourceCreateRequest,
    admin: User = Depends(require_admin),
):
    """
    Create a new source entry (metadata only).

    The source status will be "queued".  Use the upload/url endpoints
    to trigger actual ingestion.
    """
    # TODO: Implement
    raise NotImplementedError("TODO: implement create_source")


@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: str,
    body: SourceUpdateRequest,
    admin: User = Depends(require_admin),
):
    """
    Update source metadata (partial update).

    Only the fields provided in the request body will be changed.
    """
    # TODO: Implement
    raise NotImplementedError("TODO: implement update_source")


@router.delete("/{source_id}")
async def delete_source(
    source_id: str,
    admin: User = Depends(require_admin),
):
    """
    Delete a source and its chunks from the vector store.

    Returns:
        {"status": "deleted", "source_id": "..."}
    """
    # TODO: Implement
    raise NotImplementedError("TODO: implement delete_source")


@router.post("/upload", response_model=UploadResponse, status_code=201)
async def upload_source(
    file: UploadFile = File(...),
    admin: User = Depends(require_admin),
):
    """
    Upload a file and ingest it into the knowledge base.

    Supported formats: .pdf, .txt, .md

    The file is chunked, embedded, and indexed automatically.
    Returns the source ID and chunk count.
    """
    # TODO: Implement
    # Save file to disk → create Source → ingest_file(source_id, path)
    return UploadResponse(
        id="todo",
        filename=file.filename or "unknown",
        source_type="pdf",
        chunk_count=0,
        status="queued",
    )


@router.post("/url", response_model=SourceResponse, status_code=201)
async def ingest_url(
    body: dict,
    admin: User = Depends(require_admin),
):
    """
    Ingest a webpage URL into the knowledge base.

    Request body:
        {"url": "https://example.com/article", "title": "Optional title"}
    """
    # TODO: Implement
    raise NotImplementedError("TODO: implement ingest_url")
