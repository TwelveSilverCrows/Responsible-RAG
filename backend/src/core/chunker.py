"""
chunker.py — Smart document chunker
======================================
Two-tier: semantic chunking first, recursive fallback on failure or
oversized chunks.
"""

import logging

from langchain_core.documents import Document
from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

_DEFAULT_SEPARATORS: list[str] = ["\n\n", "\n", " ", "", "."]


class SmartChunker:
    """Two-tier document chunker: semantic → recursive fallback."""

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

    def chunk(self, docs: list[Document]) -> list[Document]:
        """Split *docs* into chunks. Tries semantic first, falls back to recursive."""
        if not self.use_semantic:
            return self._recursive_splitter.split_documents(docs)
        try:
            chunks = self._semantic_chunker.split_documents(docs)
            if any(len(c.page_content) > self.max_chunk_size for c in chunks):
                logger.warning("Semantic chunk exceeded max_chunk_size=%d — falling back.", self.max_chunk_size)
                return self._recursive_splitter.split_documents(docs)
            return chunks
        except Exception as exc:
            logger.warning("Semantic chunking failed (%s) — using recursive fallback.", exc)
            return self._recursive_splitter.split_documents(docs)
