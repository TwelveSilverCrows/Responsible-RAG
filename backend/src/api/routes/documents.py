"""
routes/documents.py — Document ingestion & management (public)
================================================================
Public endpoints for document ingestion (admin-only CRUD lives in
``routes/admin/sources.py``).

Endpoints:
    POST /api/v1/documents/upload  — Ingest a file (requires auth)

Low-memory notes:
    - Stream file uploads directly to chunking.
    - Process one document at a time.
"""

from fastapi import APIRouter, Depends, UploadFile, File
from src.api.schemas.source import UploadResponse
from src.api.middleware import require_current_user
from src.api.db.models import User

router = APIRouter()


@router.post("/upload", response_model=UploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(require_current_user),
):
    """
    Upload and ingest a document into the knowledge base.

    Supported formats: .pdf, .txt, .md

    The document is chunked, embedded, and stored in Chroma.
    """
    # TODO: Implement
    # from src.api.services.source_service import SourceService
    # service = SourceService()
    # source = await service.create_source({"title": file.filename, "source_type": "pdf"})
    # source = await service.ingest_file(source.id, file_path, file.filename)
    # return UploadResponse(id=source.id, filename=source.title, ...)
    return UploadResponse(
        id="todo-placeholder-id",
        filename=file.filename or "unknown",
        source_type="pdf",
        chunk_count=0,
        status="queued",
    )
