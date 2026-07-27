"""
services/source_service.py — Source management (Qdrant)
========================================================
All source metadata + status lives in Qdrant point payloads.
Processing status ("processing" → "indexed" | "error") is tracked
via placeholder points that get replaced once ingestion completes.

Flow:
    1. Upload file → placeholder points in Qdrant (status="processing")
    2. Background task → chunk & embed → replace placeholder with real
       chunks (status="indexed")
    3. On error → update placeholder payload (status="error")
"""

import asyncio
import logging
from pathlib import Path
from typing import ClassVar, Optional
from uuid import uuid4

import pymupdf4llm

from langchain_community.document_loaders import TextLoader, WebBaseLoader
from langchain_core.documents import Document

from src.core.chunker import SmartChunker
from src.core.config import get_settings
from src.core.embeddings import EmbeddingFactory
from src.core.transcriber import transcribe_async
from src.core.vector_store import KnowledgeBase
from src.core.youtube import transcribe_youtube_async

logger = logging.getLogger(__name__)


# ── Per-worker cache ─────────────────────────────────────────────────────────
# FastAPI multi-worker: each Python process keeps its own cached KnowledgeBase.
# Qdrant handles all server-side concurrency, so no locking is needed.
_kb_cache: Optional[KnowledgeBase] = None
_emb_cache = None


def _get_shared_kb() -> KnowledgeBase:
    """Return the per-worker cached KnowledgeBase instance."""
    global _kb_cache, _emb_cache
    if _kb_cache is None:
        settings = get_settings()
        _emb_cache = EmbeddingFactory.create(settings)
        _kb_cache = KnowledgeBase(settings, _emb_cache)
    return _kb_cache


class SourceService:
    """
    Knowledge-base source management — all data lives in Qdrant.
    """

    # ── Supported file type sets ──────────────────────────────────────────────
    _SUPPORTED_SUFFIXES: ClassVar[frozenset[str]] = frozenset({
        ".txt", ".pdf", ".md", ".rst", ".markdown",
        ".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".wma",
    })
    _AUDIO_SUFFIXES: ClassVar[frozenset[str]] = frozenset({
        ".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".wma",
    })

    def __init__(self):
        self._chunker: Optional[SmartChunker] = None

    # ── Lazy init ─────────────────────────────────────────────────────────────

    def _get_kb(self) -> KnowledgeBase:
        return _get_shared_kb()

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def list_sources(self) -> list[dict]:
        """Return one metadata dict per unique source in Qdrant."""
        sources = self._get_kb().list_sources()
        for src in sources:
            sid = src.get("source_id", "")
            src["chunk_count"] = self._get_kb().chunk_count(sid)
            src.setdefault("status", "indexed")
        return sources

    def get_source(self, source_id: str) -> Optional[dict]:
        """Return source metadata from Qdrant (from the first chunk)."""
        meta = self._get_kb().get_source(source_id)
        if meta:
            meta["chunk_count"] = self._get_kb().chunk_count(source_id)
            meta.setdefault("status", "indexed")
        return meta

    def create_placeholder(self, data: dict) -> dict:
        """
        Create a placeholder Qdrant point with status="processing".

        The placeholder will be replaced by the background ingestion task
        with real chunks once processing completes.

        Returns the source metadata dict (including ``source_id``).
        """
        kb = self._get_kb()
        source_id = str(uuid4())
        source_meta = {
            "source_id": source_id,
            "title": data.get("title", "Untitled"),
            "source_type": data.get("source_type", "pdf"),
            "authors": data.get("authors", []),
            "publication_date": data.get("publication_date") or "",
            "publisher": data.get("publisher") or "",
            "url": data.get("url") or "",
            "doi": data.get("doi") or "",
            "language": data.get("language") or "",
            "description": data.get("description") or "",
            "tags": data.get("tags", []),
            "content_sensitivity": data.get("content_sensitivity", "low"),
            "internal_notes": data.get("internal_notes") or "",
            "status": "processing",
            "error_message": "",
            "pending_file_path": data.get("pending_file_path", ""),
            "pending_filename": data.get("pending_filename", ""),
        }
        placeholder = [Document(page_content="", metadata={})]
        kb.add_documents(source_id, source_meta, placeholder)
        source_meta["chunk_count"] = 0
        logger.info("Created placeholder source %s (%s)", source_id, source_meta["title"])
        return source_meta

    def finalize_source(self, source_id: str, docs: list[Document],
                       override_meta: Optional[dict] = None) -> None:
        """
        Replace a placeholder with real chunks and set status="indexed".

        Called by the background ingestion task after successful processing.

        Parameters
        ----------
        override_meta:
            If provided, use this metadata dict *instead* of reading from
            Qdrant. This avoids races when the placeholder has been
            updated concurrently by a PUT request.
        """
        kb = self._get_kb()

        if override_meta is not None:
            source_meta = dict(override_meta)
        else:
            existing = kb.get_source(source_id)
            if not existing:
                logger.warning("finalize_source: source %s not found", source_id)
                return
            source_meta = dict(existing)

        # Remove old placeholder(s) — ignore if already gone (race).
        kb.delete_source(source_id)

        # Strip internal fields & mark as indexed
        for strip_key in ("chunk_index", "pending_file_path", "pending_filename"):
            source_meta.pop(strip_key, None)
        source_meta["status"] = "indexed"
        source_meta["error_message"] = ""

        kb.add_documents(source_id, source_meta, docs)
        logger.info("Finalized source %s — %d chunks indexed", source_id, len(docs))

    def fail_source(self, source_id: str, error: str) -> None:
        """Set status="error" on the placeholder (ingestion failed)."""
        kb = self._get_kb()
        kb.update_source_metadata(source_id, {
            "status": "error",
            "error_message": str(error)[:500],
        })
        logger.warning("Source %s failed: %s", source_id, error)

    def create_source(
        self, data: dict, docs: Optional[list[Document]] = None,
    ) -> dict:
        """Create a source with optional content (synchronous, status="indexed")."""
        kb = self._get_kb()
        source_id = str(uuid4())
        source_meta = {
            "source_id": source_id,
            "title": data.get("title", "Untitled"),
            "source_type": data.get("source_type", "pdf"),
            "authors": data.get("authors", []),
            "publication_date": data.get("publication_date") or "",
            "publisher": data.get("publisher") or "",
            "url": data.get("url") or "",
            "doi": data.get("doi") or "",
            "language": data.get("language") or "",
            "description": data.get("description") or "",
            "tags": data.get("tags", []),
            "content_sensitivity": data.get("content_sensitivity", "low"),
            "internal_notes": data.get("internal_notes") or "",
            "status": "indexed",
            "error_message": "",
        }
        if docs:
            kb.add_documents(source_id, source_meta, docs)
        else:
            placeholders = [Document(page_content="", metadata={})]
            kb.add_documents(source_id, source_meta, placeholders)
        source_meta["chunk_count"] = kb.chunk_count(source_id)
        logger.info("Created source %s (%s)", source_id, source_meta["title"])
        return source_meta

    def update_source(self, source_id: str, data: dict) -> Optional[dict]:
        """Update metadata on every chunk belonging to *source_id*."""
        kb = self._get_kb()
        update = {k: v for k, v in data.items() if v is not None and k != "source_id"}
        if not update:
            return kb.get_source(source_id)
        ok = kb.update_source_metadata(source_id, update)
        if not ok:
            return None
        result = kb.get_source(source_id)
        if result:
            result["chunk_count"] = kb.chunk_count(source_id)
            result.setdefault("status", "indexed")
        return result

    def delete_source(self, source_id: str) -> bool:
        """Delete every chunk with *source_id* from Qdrant."""
        return self._get_kb().delete_source(source_id)

    # ── Stats ─────────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Aggregate source statistics from Qdrant."""
        kb = self._get_kb()
        sources = kb.list_sources()
        indexed = [s for s in sources if s.get("status") in ("indexed", None)]
        errors = [s for s in sources if s.get("status") == "error"]
        processing = [s for s in sources if s.get("status") == "processing"]
        return {
            "total_sources": len(indexed),
            "indexed_sources": len(indexed),
            "processing_sources": len(processing),
            "error_sources": len(errors),
            "incomplete_metadata": sum(
                1 for s in indexed if not s.get("title") or not s.get("description")
            ),
        }

    # ── File helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _pdf_to_clean_markdown(path: Path) -> Optional[str]:
        """
        Convert a PDF to markdown and strip the reference/bibliography section.

        Academic PDFs contain lengthy reference lists that pollute the embedding
        space.  This method converts via ``pymupdf4llm`` (which preserves
        headings, lists, and structure) and trims everything from the first
        reference heading onward.

        Parameters
        ----------
        path:
            Path to the PDF file.

        Returns
        -------
        str or None
            Clean markdown text with references removed, or ``None`` on error.
        """
        import re

        try:
            import pymupdf

            doc = pymupdf.open(str(path))
        except Exception as exc:
            logger.warning("Could not open PDF '%s': %s", path.name, exc)
            return None

        try:
            md = pymupdf4llm.to_markdown(
                doc,
                header=False,
                footer=False,
                page_separators=True,
                ignore_images=True,
                write_images=False,
                image_path=None,
            )
        except Exception as exc:
            logger.warning("Could not convert PDF '%s' to markdown: %s", path.name, exc)
            doc.close()
            return None

        doc.close()

        # ── Strip reference / bibliography sections ────────────────────────
        # Common headings in academic papers
        ref_patterns = (
            r'^#{1,3}\s*(?:References|REFERENCES|Bibliography|BIBLIOGRAPHY'
            r'|Works\s+Cited|WORKS\s+CITED'
            r'|References\s+and\s+Notes|REFERENCES\s+AND\s+NOTES'
            r'|Cited\s+References|CITED\s+REFERENCES'
            r'|References\s+and\s+Further\s+Reading'
            r'|Reference\s+List|REFERENCE\s+LIST)\s*$'
        )

        lines = md.split("\n")
        ref_start = None
        for i, line in enumerate(lines):
            if re.match(ref_patterns, line.strip()):
                ref_start = i
                break

        if ref_start is not None:
            md = "\n".join(lines[:ref_start])

        # Clean up surrogate characters that pymupdf4llm can leave behind
        md = md.encode("utf-8", errors="surrogatepass").decode("utf-8", errors="ignore")

        return md.strip()

    @staticmethod
    def load_file(path: Path) -> Optional[list[Document]]:
        """Load a file into LangChain Documents. Returns None on error."""
        try:
            suffix = path.suffix.lower()
            if suffix == ".pdf":
                text = SourceService._pdf_to_clean_markdown(path)
                if not text:
                    return None
                return [Document(
                    page_content=text,
                    metadata={"source": str(path), "type": "pdf"},
                )]
            if suffix in (".txt", ".md", ".rst", ".markdown"):
                return TextLoader(str(path), encoding="utf-8").load()
        except Exception as exc:
            logger.warning("Could not load '%s': %s", path.name, exc)
        return None

    @staticmethod
    def is_supported_file(filename: str) -> bool:
        ext = Path(filename).suffix.lower()
        return ext in SourceService._SUPPORTED_SUFFIXES

    # ── Lazy chunker ──────────────────────────────────────────────────────────

    def _get_chunker(self) -> SmartChunker:
        if self._chunker is None:
            settings = get_settings()
            # Reuse the module-level embedding instance to avoid creating
            # duplicate API clients.
            emb = _emb_cache or EmbeddingFactory.create(settings)
            self._chunker = SmartChunker(
                use_semantic=settings.use_semantic_chunking,
                embedding_function=emb,
                fallback_chunk_size=settings.fallback_chunk_size,
                chunk_overlap=settings.chunk_overlap,
                max_chunk_size=settings.max_chunk_size,
            )
        return self._chunker

    # ── Async file processing (load/transcribe → chunk) ──────────────────────

    async def process_file(self, path: Path) -> Optional[list[Document]]:
        """
        Load/transcribe a single file and return its chunks.

        Handles both text/PDF (loaded synchronously via a thread-pool) and
        audio files (transcribed via Cloudflare Whisper).

        Returns ``None`` on failure.
        """
        suffix = path.suffix.lower()
        try:
            if suffix in SourceService._AUDIO_SUFFIXES:
                text = await transcribe_async(str(path))
                if not text.strip():
                    return None
                doc = Document(
                    page_content=text,
                    metadata={"source": str(path), "type": "audio"},
                )
                docs_to_chunk = [doc]
            else:
                docs = await asyncio.to_thread(self.load_file, path)
                if not docs:
                    return None
                for d in docs:
                    d.metadata.setdefault("source", str(path))
                docs_to_chunk = docs

            return self._get_chunker().chunk(docs_to_chunk)
        except Exception as exc:
            logger.warning("Failed to process '%s': %s", path.name, exc)
            return None

    async def process_youtube_url(self, url: str) -> Optional[list[Document]]:
        """
        Transcribe a YouTube URL and return its chunks.

        Returns ``None`` on failure.
        """
        try:
            text = await transcribe_youtube_async(url)
            if not text.strip():
                return None
            doc = Document(
                page_content=text,
                metadata={"source": url, "type": "youtube"},
            )
            return self._get_chunker().chunk([doc])
        except Exception as exc:
            logger.warning("Failed to transcribe YouTube '%s': %s", url, exc)
            return None

    @staticmethod
    def _web_loader_headers() -> dict[str, str]:
        """Common HTTP headers for WebBaseLoader to maximise compatibility."""
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    async def process_webpage_url(self, url: str) -> Optional[list[Document]]:
        """
        Scrape a webpage and return its chunks.

        Uses ``WebBaseLoader`` with common browser headers for broad
        compatibility.  Runs the synchronous loader in a thread-pool.

        Returns ``None`` on failure.
        """
        try:
            loader = WebBaseLoader(
                web_paths=[url],
                header_template=self._web_loader_headers(),
                requests_kwargs={"timeout": 30},
                raise_for_status=False,
            )
            docs = await asyncio.to_thread(loader.load)
            if not docs:
                return None
            for d in docs:
                d.metadata.setdefault("source", url)
                d.metadata.setdefault("type", "webpage")
            return self._get_chunker().chunk(docs)
        except Exception as exc:
            logger.warning("Failed to scrape webpage '%s': %s", url, exc)
            return None