"""
rag_chain.py — End-to-end RAG chain
======================================
:class:`RAGChain` assembles the full LCEL pipeline and exposes a simple
:meth:`invoke` interface that the UI and future API handlers can call without
knowing any LangChain internals.

Usage
-----
    from src.core.config import get_settings
    from src.core.rag_chain import RAGChain

    chain  = RAGChain(get_settings())
    result = chain.invoke("What is predictive policing?", group_prompt)
    print(result.answer)
    print(result.sources)
"""

import logging
from dataclasses import dataclass
from operator import itemgetter

from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable

from src.core.config import Settings
from src.core.embeddings import EmbeddingFactory
from src.core.retrievers import RetrieverFactory
from src.core.vector_store import KnowledgeBase

logger = logging.getLogger(__name__)


@dataclass
class RAGResult:
    """Return type for RAG chain invocation."""

    answer: str
    sources: list[dict]


def _get_source_label(doc) -> str:
    """Extract a human-readable source label from a document's metadata.

    Tries ``source_title`` first (set during ingestion from the MongoDB
    Source record), then falls back to ``title``, then ``source`` (file
    path), and finally ``"Unknown source"``.
    """
    for key in ("source_title", "title", "source"):
        value = doc.metadata.get(key)
        if value:
            return str(value)
    return "Unknown source"


def _format_docs(docs) -> str:
    """Format docs with source references for the LLM context."""
    return "\n\n".join(
        f"[{i + 1}]: {_get_source_label(doc)}\n{doc.page_content}"
        for i, doc in enumerate(docs)
    )


def _extract_source_metadata(docs) -> list[dict]:
    """Extract unique source metadata from retrieved documents.

    Returns one entry per unique source (deduplicated by ``source_id``).
    All metadata fields were stored during ingestion from the MongoDB
    Source record, so no additional database lookup is needed.
    """
    seen = set()
    sources: list[dict] = []
    for doc in docs:
        meta = doc.metadata
        sid = meta.get("source_id") or _get_source_label(doc)
        if sid in seen:
            continue
        seen.add(sid)
        sources.append({
            "source_id": sid,
            "source_title": meta.get("source_title", _get_source_label(doc)),
            "source_type": meta.get("source_type", "pdf"),
            "authors": meta.get("authors", []),
            "publication_date": meta.get("publication_date") or None,
            "publisher": meta.get("publisher") or None,
            "url": meta.get("url", ""),
            "doi": meta.get("doi", ""),
            "language": meta.get("language") or None,
            "description": meta.get("description") or None,
            "tags": meta.get("tags", []),
            "content_sensitivity": meta.get("content_sensitivity", "low"),
            "excerpt": doc.page_content[:300],
        })
    return sources


# ── Prompt template ────────────────────────────────────────────────────────────
_RAG_PROMPT = ChatPromptTemplate.from_template(
    "Conversation memory: \n{memory_context}\n"
    "Answer the question based ONLY on the following context:\n"
    "{context}\n\n"
    "Question: {question}\n\n"
    "Audience profile:\n{group_of_people}\n\n"
    "Answer: If you cannot find the answer in the context, say so clearly — "
    "do NOT fabricate information."
)


class RAGChain:
    """Retrieval-Augmented Generation chain."""

    def __init__(self, settings: Settings) -> None:
        logger.info("Initialising RAGChain (model=%s).", settings.llm_model)

        embedding_fn = EmbeddingFactory.create(settings)
        kb = KnowledgeBase(settings, embedding_fn)

        vec_retriever = kb.as_retriever(k=settings.vec_retriever_k)
        all_docs = kb.get_all_documents()
        ensemble = RetrieverFactory.build_ensemble(vec_retriever, all_docs, settings)

        llm = init_chat_model(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
        )

        self._chain = (
            {
                "memory_context": itemgetter("memory_context"),
                "context": itemgetter("question") | ensemble | _format_docs,
                "question": itemgetter("question"),
                "group_of_people": itemgetter("group_of_people")
            }
            | _RAG_PROMPT
            | llm
            | StrOutputParser()
        )

        self._ensemble = ensemble
        self._settings = settings
        logger.info("RAGChain ready.")

    @traceable(name="rag_chain_invoke", run_type="chain")
    def invoke(self, question: str, group_prompt: str, memory_context: str = "") -> RAGResult:
        """Runs the RAG pipeline and return answer with sources.
        Post-process retrieved documents so that at most ``max_returned_sources``
        are returned and documents below ``retriever_score_threshold`` are
        discarded. This implements an "up to k" behaviour using a similarity
        threshold, which you can change in the .env file.
        """
        answer = self._chain.invoke(
            {"question": question, "group_of_people": group_prompt, "memory_context": memory_context}
        )

        #retrieves candidate docs from the ensemble retriever
        docs = self._ensemble.invoke(question)
        if docs:
            d0 = docs[0]
            print("repr(d0):", repr(d0))
            print("type(d0):", type(d0))
            print("dir(d0) snippet:", [n for n in dir(d0) if not n.startswith("_")][:50])
            print("getattr score:", getattr(d0, "score", None))
            print("getattr similarity:", getattr(d0, "similarity", None))
            print("metadata keys:", list(getattr(d0, "metadata", {}).keys() if hasattr(d0, "metadata") else []))
            if isinstance(d0, dict):
                print("top-level keys (dict):", list(d0.keys()))

            # Safely convert retriever result to list
        docs_list = list(docs) if docs is not None else []

        # Helper to read metadata dict from different doc shapes (object or dict)
        def _get_metadata(d):
            if isinstance(d, dict):
                return d.get("metadata") or {}
            # some doc classes expose a .metadata attribute
            return getattr(d, "metadata", {}) or {}

        # Helper to extract a numeric score from a document's metadata (robust)
        def _get_doc_score(d):
            meta = _get_metadata(d)
            # Common locations: metadata["score"], metadata["similarity"], metadata["relevance"]
            for key in ("score", "similarity", "relevance"):
                if key in meta:
                    v = meta.get(key)
                    try:
                        return float(v)
                    except Exception:
                        pass
            # Sometimes retrievers set top-level fields (e.g., dict with 'score')
            if isinstance(d, dict) and "score" in d:
                try:
                    return float(d["score"])
                except Exception:
                    pass
            # No numeric score available
            return None

        threshold = float(getattr(self._settings, "retriever_score_threshold", 0.0) or 0.0)
        max_sources = getattr(self._settings, "max_returned_sources", None)

        # If threshold > 0: keep only docs with numeric score >= threshold. Otherwise keep all.
        if threshold > 0.0:
            filtered = [d for d in docs_list if (_get_doc_score(d) is not None and _get_doc_score(d) >= threshold)]
        else:
            filtered = docs_list

        # Sort by score descending when available; keep original order for no-score docs
        def _sort_key(d):
            s = _get_doc_score(d)
            # Put no-score docs after scored ones, but preserve their order among themselves
            return (0, ) if s is None else (1, float(s))

        # Use stable sort (Python's sort is stable) reversing by numeric value:
        # - put scored docs first sorted by score desc, then no-score docs in original order
        scored = [d for d in filtered if _get_doc_score(d) is not None]
        noscore = [d for d in filtered if _get_doc_score(d) is None]
        scored.sort(key=lambda d: _get_doc_score(d), reverse=True)
        ordered = scored + noscore

        # Cap the number of documents (apply before deduplication). If you prefer cap after dedup, slice after _extract_source_metadata.
        if max_sources is not None and max_sources > 0:
            selected = ordered[:max_sources]
        else:
            selected = ordered

        sources = _extract_source_metadata(selected)
        return RAGResult(answer=answer, sources=sources)
