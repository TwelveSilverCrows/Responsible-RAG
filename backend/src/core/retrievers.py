"""
retrievers.py — Ensemble retriever factory
============================================
Combines a dense vector-similarity retriever with a sparse BM25 keyword
retriever via :class:`EnsembleRetriever`.

Rationale
---------
* **Dense (vector)**: Captures semantic similarity — good at paraphrasing and
  concept-level matching.
* **Sparse (BM25)**: Captures exact keyword overlap — good at proper nouns,
  acronyms, and rare domain-specific terms that might be underrepresented in
  the embedding space.
* **Ensemble**: Weighted reciprocal-rank fusion of both result lists gives the
  best of both retrieval strategies.

Default weights (configurable via Settings)
-------------------------------------------
  vector 0.7 + BM25 0.3 = 1.0

Usage
-----
    ensemble = RetrieverFactory.build_ensemble(
        vec_retriever=kb.as_retriever(k=settings.vec_retriever_k),
        all_docs=kb.get_all_documents(),
        settings=settings,
    )
"""

import logging

from langchain_classic.retrievers.ensemble import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from src.core.config import Settings

logger = logging.getLogger(__name__)


class RetrieverFactory:
    """Static factory for building the ensemble retriever."""

    @staticmethod
    def build_ensemble(
        vec_retriever: BaseRetriever,
        all_docs: list[Document],
        settings: Settings,
    ) -> EnsembleRetriever:
        """
        Build and return a weighted ensemble of vector + BM25 retrievers.

        Parameters
        ----------
        vec_retriever:
            Pre-built vector-similarity retriever (e.g. from
            :meth:`KnowledgeBase.as_retriever`).
        all_docs:
            The full document corpus for building the BM25 index (in-memory).
        settings:
            Application settings — supplies ``bm25_retriever_k``,
            ``vec_weight``, and ``bm25_weight``.

        Returns
        -------
        EnsembleRetriever
            Ready-to-use ensemble retriever.
        """
        bm25 = BM25Retriever.from_documents(
            all_docs,
            search_kwargs={"k": settings.bm25_retriever_k},
        )
        logger.info(
            "Ensemble retriever ready (vec_weight=%.1f, bm25_weight=%.1f).",
            settings.vec_weight,
            settings.bm25_weight,
        )
        return EnsembleRetriever(
            retrievers=[vec_retriever, bm25],
            weights=[settings.vec_weight, settings.bm25_weight],
        )
