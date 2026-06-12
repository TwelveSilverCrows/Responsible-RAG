"""
vector_store.py — Vector-store lifecycle manager (TurboVec)
=============================================================
:class:`KnowledgeBase` owns the TurboVec vector store from initialisation
through document ingestion to retrieval and source management.  It is
the single authoritative owner of the on-disk index.

All source metadata lives in the TurboVec docstore — no external
database is required.

Usage
-----
    kb = KnowledgeBase(settings, embedding_fn)
    retriever = kb.as_retriever(k=5)
    all_docs  = kb.get_all_documents()
    sources   = kb.list_sources()
"""

import json
import logging
from pathlib import Path
from typing import Optional

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from turbovec.langchain import TurboQuantVectorStore

from src.core.chunker import SmartChunker
from src.core.config import Settings

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
        for doc in docs:
            doc.metadata["source_id"] = source_id
            doc.metadata.update(source_metadata)
        ids = self._store.add_documents(docs)
        self._id_map.setdefault(source_id, []).extend(ids)
        self._persist()
        logger.info("Stored %d document(s) for source %s", len(ids), source_id)
        return ids

    def delete_source(self, source_id: str) -> bool:
        """Delete every chunk belonging to *source_id* from the store."""
        ids = self._id_map.pop(source_id, [])
        if not ids:
            logger.warning("No chunks found for source %s", source_id)
            return False
        self._store.delete(ids)
        self._persist()
        logger.info("Deleted %d chunk(s) for source %s", len(ids), source_id)
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
        logger.info("Updated metadata on %d chunk(s) for source %s", len(ids), source_id)
        return True

    def source_count(self) -> int:
        """Return the number of unique sources."""
        return len(self._id_map)

    def chunk_count(self, source_id: str) -> int:
        """Return the number of chunks for *source_id*."""
        return len(self._id_map.get(source_id, []))

    # ── Persistence ──────────────────────────────────────────────────────────

    def _persist(self) -> None:
        """Save the vector store and ID map to disk."""
        persist_path = Path(self._settings.vectordb_dir)
        persist_path.mkdir(parents=True, exist_ok=True)
        self._store.dump(str(persist_path))
        id_map_file = persist_path / "id_map.json"
        id_map_file.write_text(json.dumps(self._id_map, indent=2))
        logger.debug("Persisted vector store to '%s'.", persist_path)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _load_or_create(self) -> None:
        """Load an existing TurboVec store or create an empty one."""
        persist_path = Path(self._settings.vectordb_dir)
        index_file = persist_path / "index.tvim"

        if index_file.exists():
            logger.info("Loading existing vector store from '%s'.", persist_path)
            self._store = TurboQuantVectorStore.load(
                str(persist_path),
                embedding=self._embedding_function,
            )
            id_map_file = persist_path / "id_map.json"
            if id_map_file.exists():
                self._id_map = json.loads(id_map_file.read_text())
            return

        logger.info("No existing store found — creating new TurboQuantVectorStore.")
        self._store = TurboQuantVectorStore(
            embedding=self._embedding_function,
            bit_width=4,
        )
        self._persist()

