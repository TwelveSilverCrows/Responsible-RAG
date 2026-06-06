"""
chunker.py — Smart document chunker
======================================
Provides :class:`SmartChunker`, which tries semantic chunking first (using
sentence-level embedding similarity) and falls back to simple
character-based recursive splitting when semantic chunking fails or produces
chunks that are too large.

Design decisions
----------------
* **Semantic-first**: Meaning-preserving boundaries produce better retrieval
  quality because the embedding model sees coherent units.
* **Size guard**: Any semantic chunk exceeding ``max_chunk_size`` characters
  triggers a full fallback, ensuring the vector store never ingests chunks
  that overflow the LLM context window.
* **Graceful degradation**: Any runtime error during semantic chunking (e.g.
  embedding model unavailable) silently falls back to recursive splitting so
  the pipeline never hard-fails at ingest time.

Usage
-----
    from src.core.config import get_settings
    from src.core.embeddings import EmbeddingFactory
    from src.core.chunker import SmartChunker

    cfg = get_settings()
    emb = EmbeddingFactory.create(cfg)
    chunker = SmartChunker(
        use_semantic=cfg.use_semantic_chunking,
        embedding_function=emb,
        fallback_chunk_size=cfg.fallback_chunk_size,
        chunk_overlap=cfg.chunk_overlap,
        max_chunk_size=cfg.max_chunk_size,
    )
    chunks = chunker.chunk(documents)
"""

import logging

from langchain_core.documents import Document
from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

_DEFAULT_SEPARATORS: list[str] = ["\n\n", "\n", " ", "", "."]


class SmartChunker:
    """
    Two-tier document chunker: semantic → recursive fallback.

    Parameters
    ----------
    use_semantic:
        Whether to attempt semantic chunking.  Set to ``False`` to always use
        the recursive splitter (useful in resource-constrained environments).
    embedding_function:
        A LangChain-compatible embeddings instance.  Required when
        ``use_semantic=True``.
    fallback_chunk_size:
        Target character count per chunk for the recursive splitter.
    chunk_overlap:
        Character overlap between consecutive recursive chunks.
    max_chunk_size:
        Semantic chunks exceeding this character length will cause the entire
        document to be re-split with the recursive fallback.
    """

    def __init__(
        self,
        use_semantic: bool = True,
        embedding_function=None,
        fallback_chunk_size: int = 1000,
        chunk_overlap: int = 200,
        max_chunk_size: int = 2000,
    ) -> None:
        self.use_semantic = use_semantic
        self.max_chunk_size = max_chunk_size

        self._semantic_chunker = SemanticChunker(
            embedding_function,
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=90,
        )
        self._recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=fallback_chunk_size,
            chunk_overlap=chunk_overlap,
            separators=_DEFAULT_SEPARATORS,
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def chunk(self, docs: list[Document]) -> list[Document]:
        """
        Split *docs* into chunks and return the result.

        Tries semantic chunking when enabled; silently falls back to recursive
        splitting on failure or oversized chunks.

        Parameters
        ----------
        docs:
            List of LangChain :class:`Document` objects to split.

        Returns
        -------
        list[Document]
            Chunked documents, each preserving the metadata of its source.
        """
        if not self.use_semantic:
            return self._recursive_fallback(docs)

        try:
            chunks = self._semantic_chunker.split_documents(docs)
            if any(len(c.page_content) > self.max_chunk_size for c in chunks):
                logger.warning(
                    "Semantic chunk exceeded max_chunk_size=%d — falling back to recursive splitter.",
                    self.max_chunk_size,
                )
                return self._recursive_fallback(docs)
            return chunks
        except Exception as exc:
            logger.warning("Semantic chunking failed (%s) — using recursive fallback.", exc)
            return self._recursive_fallback(docs)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _recursive_fallback(self, docs: list[Document]) -> list[Document]:
        """Split *docs* with the character-based recursive splitter."""
        return self._recursive_splitter.split_documents(docs)
