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
    sources: list[str]


def _format_docs(docs) -> str:
    """Format docs with source references for the LLM context."""
    return "\n\n".join(
        f"[{i + 1}]: {doc.metadata.get('title', 'unknown')}\n{doc.page_content}"
        for i, doc in enumerate(docs)
    )


def _extract_sources(docs) -> list[str]:
    """Extract unique source file paths from retrieved documents."""
    seen = set()
    return [s for doc in docs if (s := doc.metadata.get("title", "unknown")) not in seen and not seen.add(s)]


# ── Prompt template ────────────────────────────────────────────────────────────
_RAG_PROMPT = ChatPromptTemplate.from_template(
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
                "context": itemgetter("question") | ensemble | _format_docs,
                "question": itemgetter("question"),
                "group_of_people": itemgetter("group_of_people"),
            }
            | _RAG_PROMPT
            | llm
            | StrOutputParser()
        )
        self._ensemble = ensemble
        logger.info("RAGChain ready.")

    @traceable(name="rag_chain_invoke", run_type="chain")
    def invoke(self, question: str, group_prompt: str) -> RAGResult:
        """Run the RAG pipeline and return answer with sources."""
        answer = self._chain.invoke(
            {"question": question, "group_of_people": group_prompt}
        )
        # Extract sources from retrieval (re-run is minimal overhead)
        sources = _extract_sources(self._ensemble.invoke(question))
        return RAGResult(answer=answer, sources=sources)

