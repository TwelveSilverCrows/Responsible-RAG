"""
routes/documents.py — Document ingestion (public)
===================================================
Public endpoint for document upload with background processing.
Status tracked in Qdrant payload.

Endpoints:
    POST /api/v1/documents/upload  — Upload a file → background ingest
"""

from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks

from src.api.schemas.source import UploadResponse
from src.api.middleware import require_current_user
from src.api.services.source_service import SourceService

router = APIRouter()


# Reuse the same background ingest function from admin routes
from src.api.routes.admin.sources import _process_upload


@router.post("/upload", response_model=UploadResponse, status_code=202)
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(require_current_user),
):
    """
    Upload a document file → background ingestion.

    Returns immediately with status="processing".  Poll GET /admin/sources/{id}
    to see when status changes to "indexed" or "error".

    Supported formats: .pdf, .txt, .md, .rst, .markdown + audio files
    (.mp3, .wav, .m4a, .flac, .ogg, .aac, .wma).
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    service = SourceService()
    if not service.is_supported_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {Path(file.filename).suffix}. "
                   f"Supported: {', '.join(sorted(SourceService._SUPPORTED_SUFFIXES))}",
        )

    content = await file.read()
    suffix = Path(file.filename).suffix.lower()
    if suffix == ".pdf":
        source_type = "pdf"
    elif suffix in SourceService._AUDIO_SUFFIXES:
        source_type = "audio"
    else:
        source_type = "text"

    # Create placeholder (status="processing")
    meta = service.create_placeholder({
        "title": file.filename,
        "source_type": source_type,
    })

    # Schedule background processing
    background_tasks.add_task(
        _process_upload,
        source_id=meta["source_id"],
        file_content=content,
        filename=file.filename,
        title=file.filename,
    )

    return UploadResponse(
        id=meta["source_id"],
        filename=file.filename,
        source_type=source_type,
        status="processing",
        chunk_count=0,
    )
