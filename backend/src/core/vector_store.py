"""
vector_store.py — Vector-store lifecycle manager
==================================================
:class:`KnowledgeBase` owns the Chroma vector store from initialisation
through document ingestion to retrieval.  It is the single authoritative
owner of the on-disk index.

Initialisation behaviour
------------------------
1. If ``chroma_persist_dir`` already exists **and** is non-empty the store is
   opened in read-only mode — no re-indexing occurs.
2. Otherwise every supported document under ``resources_dir`` (including
   sub-directories) is loaded, chunked via :class:`SmartChunker`, and
   inserted into a freshly created store.

Supported document formats
--------------------------
* ``.txt``  — raw UTF-8 text
* ``.pdf``  — PDF (via PyMuPDF)

Usage
-----
    kb = KnowledgeBase(settings, embedding_fn)
    retriever = kb.as_retriever(k=5)
    all_docs  = kb.get_all_documents()
"""

import logging
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyMuPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever

from src.core.chunker import SmartChunker
from src.core.config import Settings

logger = logging.getLogger(__name__)

_SUPPORTED_SUFFIXES: frozenset[str] = frozenset({".txt", ".pdf"})


class KnowledgeBase:
    """
    Manages the Chroma vector store and document ingestion pipeline.

    Parameters
    ----------
    settings:
        Application settings used for paths, chunking config, etc.
    embedding_function:
        A LangChain-compatible embeddings instance used by Chroma.
    """

    def __init__(self, settings: Settings, embedding_function) -> None:
        self._settings = settings
        self._chunker = SmartChunker(
            use_semantic=settings.use_semantic_chunking,
            embedding_function=embedding_function,
            fallback_chunk_size=settings.fallback_chunk_size,
            chunk_overlap=settings.chunk_overlap,
            max_chunk_size=settings.max_chunk_size,
        )
        self._store: Chroma = self._load_or_build(embedding_function)

    # ── Public API ────────────────────────────────────────────────────────────

    def as_retriever(self, k: int = 5) -> VectorStoreRetriever:
        """
        Return a similarity-search retriever over the vector store.

        Parameters
        ----------
        k:
            Number of documents to retrieve per query.
        """
        return self._store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k},
        )

    def get_all_documents(self) -> list[Document]:
        """
        Return every document currently stored in the vector index.

        Used to build the BM25 retriever which needs in-memory access to the
        full corpus.
        """
        raw = self._store.get(include=["metadatas", "documents"])
        return [
            Document(page_content=text, metadata=meta or {}, id=doc_id)
            for text, meta, doc_id in zip(
                raw["documents"], raw["metadatas"], raw["ids"]
            )
        ]

    # ── Private helpers ───────────────────────────────────────────────────────

    def _load_or_build(self, embedding_function) -> Chroma:
        """Open the existing store or build a new one from ``resources_dir``."""
        persist_path = Path(self._settings.chroma_persist_dir)
        store = Chroma(
            embedding_function=embedding_function,
            persist_directory=self._settings.chroma_persist_dir,
        )

        already_indexed = persist_path.exists() and any(persist_path.iterdir())
        if already_indexed:
            logger.info("Loaded existing vector store from '%s'.", persist_path)
            return store

        logger.info(
            "Building new vector store from resources at '%s'.",
            self._settings.resources_dir,
        )
        resources = Path(self._settings.resources_dir)
        if not resources.exists():
            logger.warning(
                "Resources directory '%s' not found — store will be empty.", resources
            )
            return store

        ingested = 0
        for file_path in resources.glob("**/*"):
            if file_path.suffix.lower() not in _SUPPORTED_SUFFIXES:
                continue
            docs = self._load_file(file_path)
            if not docs:
                continue
            for doc in docs:
                doc.metadata["source"] = str(file_path)
            chunks = self._chunker.chunk(docs)
            store.add_documents(chunks)
            ingested += 1
            logger.debug("Indexed %s (%d chunks)", file_path.name, len(chunks))

        logger.info("Ingested %d document(s) into the vector store.", ingested)
        return store

    @staticmethod
    def _load_file(path: Path) -> list[Document] | None:
        """
        Load a single file into a list of LangChain Documents.

        Returns ``None`` on any loading error so the caller can skip the file.
        """
        try:
            if path.suffix.lower() == ".txt":
                return TextLoader(str(path)).load()
            if path.suffix.lower() == ".pdf":
                return PyMuPDFLoader(str(path)).load()
        except Exception as exc:
            logger.warning("Could not load '%s': %s", path.name, exc)
        return None
