"""
schemas/source.py — Knowledge-base source documents
=====================================================
Metadata plus lightweight status tracking (stored in Qdrant payload).
"""

from pydantic import BaseModel, Field
from typing import Optional


SourceType = str   # "pdf" | "text" | "audio" | "webpage" | "youtube"
ContentSensitivity = str  # "low" | "medium" | "high"


class SourceCreateRequest(BaseModel):
    """Create / ingest a new source document."""

    title: str = Field(..., min_length=1, max_length=300, description="Document title.")
    source_type: str = Field(
        ..., description="Type of source.",
        example="pdf",
    )
    authors: list[str] = Field(
        default_factory=list, description="Author names.",
    )
    publication_date: Optional[str] = Field(None, description="Publication date (ISO-8601 or year).")
    publisher: Optional[str] = Field(None, max_length=200)
    url: str = Field(..., min_length=1, description="Source URL (required).")
    doi: Optional[str] = Field(None, description="Digital Object Identifier.")
    language: Optional[str] = Field(None, description="Language code (e.g. 'en', 'fr').")
    description: Optional[str] = Field(None, max_length=2000)
    tags: list[str] = Field(default_factory=list)
    content_sensitivity: str = Field(
        "low", description="'low', 'medium', or 'high'.",
    )
    internal_notes: Optional[str] = Field(None, max_length=2000)


class SourceUpdateRequest(BaseModel):
    """Partial update to a source document's metadata."""

    title: Optional[str] = Field(None, max_length=300)
    authors: Optional[list[str]] = Field(None)
    publication_date: Optional[str] = Field(None)
    publisher: Optional[str] = Field(None, max_length=200)
    url: Optional[str] = Field(None)
    doi: Optional[str] = Field(None)
    language: Optional[str] = Field(None)
    description: Optional[str] = Field(None, max_length=2000)
    tags: Optional[list[str]] = Field(None)
    content_sensitivity: Optional[str] = Field(None)
    internal_notes: Optional[str] = Field(None, max_length=2000)


class SourceResponse(BaseModel):
    """Source metadata as stored in Qdrant point payload."""

    source_id: str = Field(..., alias="id")
    title: str = Field(...)
    source_type: str = Field(...)
    authors: list[str] = Field(default_factory=list)
    publication_date: Optional[str] = None
    publisher: Optional[str] = None
    url: str = Field("")
    doi: Optional[str] = None
    language: Optional[str] = None
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    content_sensitivity: str = Field("low")
    internal_notes: Optional[str] = None
    status: str = Field("indexed")
    error_message: Optional[str] = None
    chunk_count: int = Field(0)

    model_config = {"populate_by_name": True}


class SourceListResponse(BaseModel):
    """Paginated list of sources."""

    sources: list[SourceResponse] = Field(default_factory=list)
    total: int = Field(0)
    page: int = Field(1)
    limit: int = Field(20)


class URLUploadRequest(BaseModel):
    """Submit a URL (webpage / YouTube) for background processing."""

    url: str = Field(..., description="Source URL.")
    title: str = Field(..., min_length=1, max_length=300, description="Source title.")
    source_type: str = Field("webpage", description="'webpage' or 'youtube'.")
    authors: list[str] = Field(default_factory=list)
    publication_date: Optional[str] = Field(None)
    publisher: Optional[str] = Field(None, max_length=200)
    language: Optional[str] = Field(None)
    description: Optional[str] = Field(None, max_length=2000)
    tags: list[str] = Field(default_factory=list)
    content_sensitivity: str = Field("low")
    internal_notes: Optional[str] = Field(None, max_length=2000)


class YouTubeUploadRequest(BaseModel):
    """Submit a YouTube URL for background transcription and ingestion."""
    url: str = Field(..., description="YouTube video URL.")
    title: str = Field(..., min_length=1, max_length=300, description="Source title.")
    authors: list[str] = Field(default_factory=list)
    publication_date: Optional[str] = Field(None)
    publisher: Optional[str] = Field(None, max_length=200)
    language: Optional[str] = Field(None)
    description: Optional[str] = Field(None, max_length=2000)
    tags: list[str] = Field(default_factory=list)
    content_sensitivity: str = Field("low")
    internal_notes: Optional[str] = Field(None, max_length=2000)


class UploadResponse(BaseModel):
    """Response after uploading a file for ingestion."""

    id: str = Field(..., description="Source document ID.")
    filename: str = Field(..., description="Original filename.")
    source_type: str = Field(..., description="Detected source type.")
    status: str = Field("processing", description="'processing' | 'indexed' | 'error'.")
    chunk_count: int = Field(0, description="Number of chunks generated.")
