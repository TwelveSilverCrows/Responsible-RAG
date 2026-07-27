"""
routes/admin/sources.py — Admin source management
===================================================
All data lives in Qdrant — status tracked via placeholder points.

Endpoints:
    GET    /api/v1/admin/sources           — List all sources
    GET    /api/v1/admin/sources/{id}      — Get source details
    POST   /api/v1/admin/sources           — Create source (metadata only)
    PUT    /api/v1/admin/sources/{id}      — Update source metadata
    DELETE /api/v1/admin/sources/{id}      — Delete source (all chunks)
    POST   /api/v1/admin/sources/upload    — Upload file → background ingest
    POST   /api/v1/admin/sources/webpage   — Webpage URL → background scrape
    POST   /api/v1/admin/sources/youtube   — YouTube URL → background ingest

Admin-only (all endpoints require admin role).
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException

from src.api.schemas.source import (
    SourceResponse,
    SourceListResponse,
    SourceCreateRequest,
    SourceUpdateRequest,
    UploadResponse,
    URLUploadRequest,
    YouTubeUploadRequest,
)
from src.api.middleware import require_admin
from src.api.services.source_service import SourceService
from src.core.config import get_settings

# Dedicated thread pool for CPU-bound background ingest tasks so they
# never block the asyncio event loop.
_background_executor = ThreadPoolExecutor(max_workers=2)

logger = logging.getLogger(__name__)

router = APIRouter()


def _meta_to_response(meta: dict) -> SourceResponse:
    """Convert a metadata dict from Qdrant payload to a SourceResponse."""
    return SourceResponse(
        id=meta.get("source_id", ""),
        title=meta.get("title", ""),
        source_type=meta.get("source_type", "pdf"),
        authors=meta.get("authors", []),
        publication_date=meta.get("publication_date") or None,
        publisher=meta.get("publisher") or None,
        url=meta.get("url") or "",
        doi=meta.get("doi") or None,
        language=meta.get("language") or None,
        description=meta.get("description") or None,
        tags=meta.get("tags", []),
        content_sensitivity=meta.get("content_sensitivity", "low"),
        internal_notes=meta.get("internal_notes") or None,
        status=meta.get("status", "indexed"),
        error_message=meta.get("error_message") or None,
        chunk_count=meta.get("chunk_count", 0),
    )


@router.get("", response_model=SourceListResponse)
def list_sources(
    page: int = 1,
    limit: int = 20,
    admin: dict = Depends(require_admin),
):
    """List all knowledge-base sources (from Qdrant payload).

    If the embedding API is in cooldown (quota exhausted), the endpoint
    still returns the source list — it reads from Qdrant
    and does **not** call the embedding API.
    """
    service = SourceService()
    try:
        sources = service.list_sources()
    except Exception:
        logger.exception("Unexpected error listing sources")
        raise HTTPException(status_code=500, detail="Failed to list sources")

    total = len(sources)
    start = (page - 1) * limit
    paged = sources[start: start + limit]
    return SourceListResponse(
        sources=[_meta_to_response(s) for s in paged],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{source_id}", response_model=SourceResponse)
def get_source(
    source_id: str,
    admin: dict = Depends(require_admin),
):
    """Get detailed metadata for a single source.

    This endpoint reads from Qdrant and does **not**
    call the embedding API, so it works even during cooldown.
    """
    service = SourceService()
    try:
        meta = service.get_source(source_id)
    except Exception:
        logger.exception("Unexpected error getting source")
        raise HTTPException(status_code=500, detail="Failed to get source")
    if meta is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return _meta_to_response(meta)


@router.post("", response_model=SourceResponse, status_code=201)
def create_source(
    body: SourceCreateRequest,
    admin: dict = Depends(require_admin),
):
    """Create a new source with metadata (synchronous, status='indexed')."""
    service = SourceService()
    meta = service.create_source(body.model_dump())
    return _meta_to_response(meta)


@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: str,
    body: SourceUpdateRequest,
    admin: dict = Depends(require_admin),
):
    """Update source metadata and trigger background processing if a pending file exists."""
    service = SourceService()
    meta = service.update_source(source_id, body.model_dump(exclude_none=True))
    if meta is None:
        raise HTTPException(status_code=404, detail="Source not found")

    # If the placeholder has a pending file, start background processing now
    # (same strategy as YouTube — metadata is ready, so kick off ingestion).
    pending_path = meta.get("pending_file_path")
    if pending_path:
        path = Path(pending_path)
        if path.exists():
            file_content = path.read_bytes()
            orig_filename = meta.get("pending_filename", path.name)
            path.unlink(missing_ok=True)

            # Clear the pending flag so processing isn't triggered again
            service._get_kb().update_source_metadata(source_id, {
                "pending_file_path": "",
                "pending_filename": "",
            })

            loop = asyncio.get_event_loop()
            # Pass the full metadata snapshot to avoid a race with the
            # background thread reading stale data from Qdrant.
            loop.run_in_executor(
                _background_executor,
                _process_upload,
                source_id,
                file_content,
                orig_filename,
                meta.get("title", orig_filename),
                meta,  # full metadata snapshot
            )

    return _meta_to_response(meta)


@router.delete("/{source_id}")
def delete_source(
    source_id: str,
    admin: dict = Depends(require_admin),
):
    """Delete a source and all its chunks from Qdrant."""
    service = SourceService()
    deleted = service.delete_source(source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Source not found")
    return {"status": "deleted", "source_id": source_id}


# ── Background ingestion task ────────────────────────────────────────────────

def _process_upload(
    source_id: str,
    file_content: bytes,
    filename: str,
    title: str,
    source_meta: Optional[dict] = None,
) -> None:
    """
    Background task: save to temp → process (load/transcribe + chunk)
    → finalize source in Qdrant.

    Uses ``SourceService.process_file`` for all file types (text, PDF, audio).
    Runs outside the request-response cycle.

    If the embedding API is in cooldown, the file is still processed using
    recursive chunking (no semantic chunking).  The source is indexed
    without waiting for the cooldown to expire.

    Parameters
    ----------
    source_meta:
        Optional full metadata snapshot captured at call time so the
        background thread does not need to re-read from Qdrant
        (avoids races with concurrent PUT metadata updates).
    """
    service = SourceService()
    try:
        settings = get_settings()
        tmp = Path(settings.upload_dir) / f"bg_{os.urandom(8).hex()}_{filename}"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_bytes(file_content)
        try:
            chunks = asyncio.run(service.process_file(tmp))
        finally:
            tmp.unlink(missing_ok=True)

        if not chunks:
            service.fail_source(source_id, "Processing returned no chunks")
            return

        service.finalize_source(source_id, chunks, override_meta=source_meta)
        logger.info("Background ingest complete for source %s (%d chunks)", source_id, len(chunks))

    except Exception as exc:
        logger.error("Background ingest failed for source %s: %s", source_id, exc)
        service.fail_source(source_id, str(exc))


def _process_youtube_upload(
    source_id: str,
    url: str,
    title: str,
) -> None:
    """
    Background task: transcribe YouTube audio → chunk → finalize source.

    Runs outside the request-response cycle.  If the embedding API is in
    cooldown, the transcription is still chunked using the recursive
    fallback (no semantic chunking).
    """
    service = SourceService()
    try:
        chunks = asyncio.run(service.process_youtube_url(url))
        if not chunks:
            service.fail_source(source_id, "YouTube transcription returned no content")
            return

        service.finalize_source(source_id, chunks)
        logger.info("Background YouTube ingest complete for source %s (%d chunks)", source_id, len(chunks))

    except Exception as exc:
        logger.error("Background YouTube ingest failed for source %s: %s", source_id, exc)
        service.fail_source(source_id, str(exc))


@router.post("/upload", response_model=UploadResponse, status_code=202)
async def upload_source(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    admin: dict = Depends(require_admin),
):
    """
    Upload a file → background ingestion.

    Returns immediately with status="processing".  Poll GET /{id} to
    see when status changes to "indexed" or "error".

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

    # File size limits per type
    _SIZE_LIMITS = {
        "pdf":   100 * 1024 * 1024,   # 100 MB
        "audio": 500 * 1024 * 1024,   # 500 MB
        "text":   15 * 1024 * 1024,   #  15 MB
    }

    suffix = Path(file.filename).suffix.lower()
    if suffix == ".pdf":
        source_type = "pdf"
    elif suffix in SourceService._AUDIO_SUFFIXES:
        source_type = "audio"
    else:
        source_type = "text"

    limit = _SIZE_LIMITS.get(source_type, 50 * 1024 * 1024)
    if file.size is not None and file.size > limit:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size for {source_type.upper()} files is {limit // (1024 * 1024)}MB.",
        )

    content = await file.read()
    if len(content) > limit:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size for {source_type.upper()} files is {limit // (1024 * 1024)}MB.",
        )

    # Save file to a temporary location and create a placeholder.
    # Processing is NOT started here — it will be triggered when the
    # user submits metadata via PUT /{id} (same strategy as YouTube).
    settings = get_settings()
    tmp_dir = Path(settings.upload_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = tmp_dir / f"pending_{os.urandom(8).hex()}_{file.filename}"
    tmp_path.write_bytes(content)

    meta = service.create_placeholder({
        "title": title or file.filename,
        "source_type": source_type,
        "pending_file_path": str(tmp_path),
        "pending_filename": file.filename,
    })

    return UploadResponse(
        id=meta["source_id"],
        filename=file.filename,
        source_type=source_type,
        status="processing",
        chunk_count=0,
    )


def _process_webpage_upload(
    source_id: str,
    url: str,
    title: str,
) -> None:
    """
    Background task: scrape webpage → chunk → finalize source.

    Runs outside the request-response cycle.  If the embedding API is in
    cooldown, the content is still chunked using the recursive fallback
    (no semantic chunking).
    """
    service = SourceService()
    try:
        chunks = asyncio.run(service.process_webpage_url(url))
        if not chunks:
            service.fail_source(source_id, "Webpage scraping returned no content")
            return

        service.finalize_source(source_id, chunks)
        logger.info("Background webpage ingest complete for source %s (%d chunks)", source_id, len(chunks))

    except Exception as exc:
        logger.error("Background webpage ingest failed for source %s: %s", source_id, exc)
        service.fail_source(source_id, str(exc))


@router.post("/webpage", response_model=UploadResponse, status_code=202)
async def upload_webpage(
    body: URLUploadRequest,
    admin: dict = Depends(require_admin),
):
    """
    Submit a webpage URL → background scraping & ingestion.

    Returns immediately with status="processing".  Poll GET /{id} to
    see when status changes to "indexed" or "error".
    """
    service = SourceService()

    meta = service.create_placeholder({
        "title": body.title,
        "source_type": "webpage",
        "authors": body.authors,
        "publication_date": body.publication_date,
        "publisher": body.publisher or "",
        "url": body.url,
        "language": body.language,
        "description": body.description,
        "tags": body.tags,
        "content_sensitivity": body.content_sensitivity,
        "internal_notes": body.internal_notes,
    })

    loop = asyncio.get_event_loop()
    loop.run_in_executor(
        _background_executor,
        _process_webpage_upload,
        meta["source_id"],
        body.url,
        body.title,
    )

    return UploadResponse(
        id=meta["source_id"],
        filename=body.url,
        source_type="webpage",
        status="processing",
        chunk_count=0,
    )


@router.post("/youtube", response_model=UploadResponse, status_code=202)
async def upload_youtube(
    body: YouTubeUploadRequest,
    admin: dict = Depends(require_admin),
):
    """
    Submit a YouTube URL → background transcription & ingestion.

    Returns immediately with status="processing".  Poll GET /{id} to
    see when status changes to "indexed" or "error".
    """
    service = SourceService()

    # Create placeholder (status="processing")
    meta = service.create_placeholder({
        "title": body.title,
        "source_type": "youtube",
        "authors": body.authors,
        "publication_date": body.publication_date,
        "publisher": body.publisher or "YouTube",
        "url": body.url,
        "language": body.language,
        "description": body.description,
        "tags": body.tags,
        "content_sensitivity": body.content_sensitivity,
        "internal_notes": body.internal_notes,
    })

    # Schedule background YouTube processing in thread pool
    loop = asyncio.get_event_loop()
    loop.run_in_executor(
        _background_executor,
        _process_youtube_upload,
        meta["source_id"],
        body.url,
        body.title,
    )

    return UploadResponse(
        id=meta["source_id"],
        filename=body.url,
        source_type="youtube",
        status="processing",
        chunk_count=0,
    )
