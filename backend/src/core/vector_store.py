"""
vector_store.py — Vector-store lifecycle manager (TurboVec)
=============================================================
:class:`KnowledgeBase` owns the TurboVec vector store from initialisation
through document ingestion to retrieval and source management.  It is
the single authoritative owner of the on-disk index.

All source metadata lives in the TurboVec docstore — no external
database is required.

Concurrency
-----------
All **write** operations (add, delete, update metadata, persist) are
serialised through a :class:`threading.Lock` so that concurrent requests
or background tasks never corrupt the in-memory store or its on-disk
files.  **Read** operations (list, get, count) proceed without locking
and may see a slightly stale snapshot during an active write — this is
acceptable for the admin UI.

Embedding validation
--------------------
Before accepting new documents, :meth:`add_documents` performs a quick
sanity check on a sample embedding to guard against corrupted API
responses (NaN, all-zeros, wrong dimensions).

Usage
-----
    kb = KnowledgeBase(settings, embedding_fn)
    retriever = kb.as_retriever(k=5)
    all_docs  = kb.get_all_documents()
    sources   = kb.list_sources()
"""

import json
import logging
import os
import threading
from pathlib import Path
from typing import Optional

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from turbovec.langchain import TurboQuantVectorStore

from src.core.chunker import SmartChunker
from src.core.config import Settings
from src.core.embeddings import EmbeddingValidationError, validate_embedding

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """
    Manages the TurboVec vector store, document ingestion, and source CRUD.

    All source metadata is stored in the TurboVec docstore — no MongoDB.

    Parameters
    ----------
    settings:
        Application settings used for paths, chunking config, etc.
    embedding_function:
        A LangChain-compatible embeddings instance used by TurboVec.
    """

    def __init__(
        self, settings: Settings, embedding_function,
    ) -> None:
        self._settings = settings
        self._embedding_function = embedding_function
        self._chunker = SmartChunker(
            use_semantic=settings.use_semantic_chunking,
            embedding_function=embedding_function,
            fallback_chunk_size=settings.fallback_chunk_size,
            chunk_overlap=settings.chunk_overlap,
            max_chunk_size=settings.max_chunk_size,
        )
        # source_id → list of document IDs in the vector store
        self._id_map: dict[str, list[str]] = {}
        self._store: TurboQuantVectorStore
        # ── Write serialisation lock ────────────────────────────────────────
        # All methods that mutate the store acquire this lock so concurrent
        # background tasks and API requests don't corrupt the in-memory state
        # or the on-disk files.
        self._write_lock = threading.Lock()
        self._load_or_create()

    # ── Public API ────────────────────────────────────────────────────────────

    def as_retriever(self, k: int = 5) -> VectorStoreRetriever:
        return self._store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k},
        )

    def get_all_documents(self) -> list[Document]:
        """Return every document currently stored in the vector index."""
        all_ids = [
            doc_id for ids in self._id_map.values() for doc_id in ids
        ]
        if not all_ids:
            return []
        return self._store.get_by_ids(all_ids)

    # ── Source CRUD (all metadata lives in TurboVec docstore) ─────────────────

    def add_documents(
        self, source_id: str, source_metadata: dict, docs: list[Document],
    ) -> list[str]:
        """
        Store documents (chunks) in TurboVec with source metadata attached.

        Performs a lightweight embedding validation before enqueuing the
        write — if the embedding function returns corrupted vectors the
        operation is rejected early.

        Parameters
        ----------
        source_id:
            Unique identifier for the source.  Used to group chunks.
        source_metadata:
            Source-level fields (title, authors, tags, …) applied to every
            chunk so that retrieved chunks carry full citation info.
        docs:
            LangChain Document objects to store (pre-chunked).

        Returns
        -------
        list[str]
            TurboVec document IDs for the stored documents.
        """
        # ── Embedding sanity check ────────────────────────────────────────────
        # Embed a short sample to verify the API is returning valid vectors
        # **before** we touch the store.  This catches corrupted API responses
        # (NaN, all-zeros, cooldown) without wasting a full batch.
        if docs:
            self._validate_embedding_sample()

        with self._write_lock:
            for doc in docs:
                doc.metadata["source_id"] = source_id
                doc.metadata.update(source_metadata)
            ids = self._store.add_documents(docs)
            self._id_map.setdefault(source_id, []).extend(ids)
            self._persist()
            logger.info(
                "Stored %d document(s) for source %s",
                len(ids), source_id,
            )
            return ids

    def delete_source(self, source_id: str) -> bool:
        """Delete every chunk belonging to *source_id* from the store."""
        with self._write_lock:
            ids = self._id_map.pop(source_id, [])
            if not ids:
                logger.warning("No chunks found for source %s", source_id)
                return False
            self._store.delete(ids)
            self._persist()
            logger.info(
                "Deleted %d chunk(s) for source %s", len(ids), source_id,
            )
            return True

    def get_source(self, source_id: str) -> Optional[dict]:
        """Return the source metadata for *source_id* (from the first chunk)."""
        ids = self._id_map.get(source_id, [])
        if not ids:
            return None
        docs = self._store.get_by_ids([ids[0]])
        if docs:
            return dict(docs[0].metadata)
        return None

    def list_sources(self) -> list[dict]:
        """
        Return one metadata dict per unique ``source_id`` in the store.

        Deduplicates by ``source_id`` so each source appears once.
        """
        sources: list[dict] = []
        for source_id in self._id_map:
            ids = self._id_map[source_id]
            if not ids:
                continue
            docs = self._store.get_by_ids([ids[0]])
            if docs:
                sources.append(dict(docs[0].metadata))
        return sources

    def update_source_metadata(self, source_id: str, metadata: dict) -> bool:
        """
        Update metadata on **every** chunk belonging to *source_id*.

        Fields in *metadata* are merged into existing metadata (upsert).
        TurboVec does not support partial metadata updates, so chunks
        are re-added with merged metadata.
        """
        with self._write_lock:
            ids = self._id_map.get(source_id, [])
            if not ids:
                return False

            docs = self._store.get_by_ids(ids)
            if not docs:
                return False

            # Merge metadata on each doc
            for doc in docs:
                doc.metadata = {**doc.metadata, **metadata}

            # Remove old entries and re-add with merged metadata
            self._store.delete(ids)
            new_ids = self._store.add_documents(docs)
            self._id_map[source_id] = new_ids
            self._persist()
            logger.info(
                "Updated metadata on %d chunk(s) for source %s",
                len(ids), source_id,
            )
            return True

    def source_count(self) -> int:
        """Return the number of unique sources."""
        return len(self._id_map)

    def chunk_count(self, source_id: str) -> int:
        """Return the number of chunks for *source_id*."""
        return len(self._id_map.get(source_id, []))

    # ── Embedding validation ─────────────────────────────────────────────────

    def _validate_embedding_sample(self) -> None:
        """
        Embed a short probe string and validate the result.

        This catches corrupted API responses (NaN, all-zeros, wrong
        dimensions) **before** we call ``add_documents`` so the write
        lock is never even contended with bad data.

        Raises :class:`EmbeddingValidationError` on corrupted output.
        """
        try:
            result = self._embedding_function.embed_query("probe")
            validate_embedding(result, label="add_documents probe")
        except EmbeddingValidationError:
            raise
        except Exception as exc:
            logger.warning("Embedding probe failed: %s", exc)
            # Don't block ingestion for transient errors — the actual
            # ``add_documents`` call inside TurboVec will surface them.
            # Only raise for clear corruption signals.
            raise EmbeddingValidationError(
                f"Embedding probe failed — rejecting write: {exc}"
            ) from exc

    # ── Persistence (atomic write) ───────────────────────────────────────────

    def _persist(self) -> None:
        """
        Save the vector store and ID map to disk using atomic writes.

        Writes to a temporary location first, then renames into place.
        This prevents the corruption that occurs when a process is killed
        mid-write or concurrent persistence operations overlap.
        """
        persist_path = Path(self._settings.vectordb_dir)
        persist_path.mkdir(parents=True, exist_ok=True)

        # ── TurboVec store (dump to temp dir, then swap files) ────────────
        tmp_dir = persist_path / ".tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        import tempfile

        with tempfile.TemporaryDirectory(dir=str(tmp_dir)) as tmp_str:
            tmp_path = Path(tmp_str)
            self._store.dump(str(tmp_path))
            for fname in ("docstore.json", "index.tvim"):
                src = tmp_path / fname
                dst = persist_path / fname
                if src.exists():
                    src.replace(dst)

        # ── id_map.json (atomic write) ────────────────────────────────────
        id_map_tmp = tmp_dir / f"id_map_{os.urandom(8).hex()}.json"
        id_map_tmp.write_text(json.dumps(self._id_map, indent=2))
        id_map_tmp.replace(persist_path / "id_map.json")

        # Clean up temp dir
        import shutil

        shutil.rmtree(tmp_dir, ignore_errors=True)

        logger.debug("Persisted vector store to '%s'.", persist_path)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _load_or_create(self) -> None:
        """
        Load an existing TurboVec store or create a fresh one.

        If the store files are corrupted (e.g. by a previous interrupted
        write), they are backed up with a ``.corrupted`` suffix and a new
        empty store is created so the application can continue operating.
        """
        persist_path = Path(self._settings.vectordb_dir)
        index_file = persist_path / "index.tvim"

        if not index_file.exists():
            logger.info("No existing store found — creating new TurboQuantVectorStore.")
            self._store = TurboQuantVectorStore(
                embedding=self._embedding_function,
                bit_width=4,
            )
            self._persist()
            return

        # ── Attempt to load the existing store ───────────────────────────
        try:
            logger.info("Loading existing vector store from '%s'.", persist_path)
            self._store = TurboQuantVectorStore.load(
                str(persist_path),
                embedding=self._embedding_function,
            )
            id_map_file = persist_path / "id_map.json"
            if id_map_file.exists():
                self._id_map = json.loads(id_map_file.read_text())
            return

        except (json.JSONDecodeError, KeyError, ValueError, OSError) as exc:
            logger.critical(
                "Vector store at '%s' is corrupted (%s). "
                "Backing up and creating a fresh store. "
                "Some indexed sources may be lost.",
                persist_path,
                exc,
            )
            # Back up corrupted files for forensic analysis
            import shutil

            backup_dir = persist_path.parent / f"vectordb_corrupted_{os.urandom(4).hex()}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            for f in persist_path.glob("*"):
                if f.name != ".gitkeep" and f.is_file():
                    shutil.copy2(str(f), str(backup_dir / f.name))
            logger.info("Corrupted store backed up to '%s'.", backup_dir)

            # Clear the store directory (except .gitkeep)
            for f in persist_path.glob("*"):
                if f.name != ".gitkeep":
                    if f.is_file():
                        f.unlink()
                    elif f.is_dir():
                        shutil.rmtree(str(f), ignore_errors=True)

            # Create fresh store
            self._store = TurboQuantVectorStore(
                embedding=self._embedding_function,
                bit_width=4,
            )
            self._id_map = {}
            self._persist()
            logger.info("Fresh vector store created at '%s'.", persist_path)

