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
In-memory state is serialised by an instance-level ``_write_lock``.
On-disk persistence is serialised by the **module-level** ``_persist_lock``
so concurrent ``KnowledgeBase`` instances (from separate requests) never
race on the same directory.

Embedding validation
--------------------
Before accepting new documents, :meth:`add_documents` performs a quick
sanity check on a sample embedding to guard against corrupted API
responses (NaN, all-zeros, wrong dimensions).
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

# Module-level lock: serialises all on-disk writes across every
# KnowledgeBase instance so concurrent requests never race on the
# same vector-store directory or id_map.json.
_persist_lock = threading.Lock()


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
        # Guards the in-memory _id_map and _store against concurrent
        # mutations from background tasks and API requests.
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

    # ── Persistence (direct write, serialised across instances) ─────────────

    def _persist(self) -> None:
        """
        Write the current in-memory state to disk.

        The module-level ``_persist_lock`` ensures that only one
        ``KnowledgeBase`` instance writes to the vector-store directory
        at a time, eliminating races between concurrent requests.
        """
        persist_path = Path(self._settings.vectordb_dir)
        persist_path.mkdir(parents=True, exist_ok=True)

        with _persist_lock:
            self._store.dump(str(persist_path))
            (persist_path / "id_map.json").write_text(
                json.dumps(self._id_map, indent=2),
            )

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
            # Use a subdirectory inside persist_path because the parent
            # directory (/storage/) may be a Docker mount point owned by
            # root and not writable by the app user.
            import shutil

            backup_dir = persist_path / f".corrupted_{os.urandom(4).hex()}"
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

