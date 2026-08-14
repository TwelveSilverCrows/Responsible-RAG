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

        #helper to extract a numeric score from a document's metadata
        def _get_doc_score(d):
            meta = getattr(d, "metadata", {}) or {}
            for key in ("score", "similarity", "relevance"):
                v = meta.get(key)
                if v is not None:
                    try:
                        return float(v)
                    except Exception:
                        pass
            return None

        threshold = getattr(self._settings, "retriever_score_threshold", 0.0)
        max_sources = getattr(self._settings, "max_returned_sources", None)

        #filter by threshold
        if threshold and threshold > 0.0:
            filtered = [d for d in docs if (_get_doc_score(d) is not None and _get_doc_score(d) >= threshold)]
        else:
            filtered = list(docs)

        #sort by score descending when score available else preserve original order
        def _sort_key(d):
            s = _get_doc_score(d)
            return s if s is not None else float("-inf")

        filtered.sort(key=_sort_key, reverse=True)

        # Apply maximum cap (None is no cap)
        if max_sources is not None and max_sources > 0:
            selected = filtered[: max_sources]
        else:
            selected = filtered

        sources = _extract_source_metadata(selected)
        return RAGResult(answer=answer, sources=sources)
