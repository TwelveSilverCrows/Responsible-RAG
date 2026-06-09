"""
routes/search.py — Standalone search endpoint
===============================================
Direct access to the hybrid retriever without LLM generation. Useful for
debugging, evaluation, or building custom UX on top of the retrieval layer.

Endpoints:
    POST /api/v1/search  — Retrieve relevant chunks for a query

Low-memory notes:
    - Limit top_k to small values (3-10) to reduce memory per request.
    - Return only chunk text + metadata, not full documents.
"""

from fastapi import APIRouter, Depends
from src.api.schemas.chat import ChatRequest
from src.api.deps import get_rag_chain
from src.api.middleware import get_current_user
from src.api.db.models import User
from src.core.rag_chain import RAGChain
from pydantic import BaseModel, Field
from typing import Optional


class SearchRequest(BaseModel):
    """Standalone search request."""
    query: str = Field(..., min_length=1, max_length=1024)
    top_k: int = Field(default=5, ge=1, le=20)
    profile_key: Optional[str] = None


class RetrievedChunk(BaseModel):
    """A single search result chunk."""
    text: str = Field(...)
    score: float = Field(...)
    source: str = Field("")
    chunk_id: str = Field("")


class SearchResponse(BaseModel):
    """Search response."""
    query: str = Field(...)
    results: list[RetrievedChunk] = Field(default_factory=list)
    total: int = Field(0)


router = APIRouter()


@router.post("", response_model=SearchResponse)
async def search(
    body: SearchRequest,
    chain: RAGChain = Depends(get_rag_chain),
    user: User | None = Depends(get_current_user),
):
    """
    Retrieve the most relevant chunks for a given query.

    Uses the hybrid ensemble retriever (vector + BM25) without summarising
    through an LLM. Returns raw chunk content and metadata.
    """
    # TODO: Implement hybrid retrieval
    # results = chain.retriever.invoke(body.query, k=body.top_k)
    # chunks = [RetrievedChunk(text=r.page_content, score=r.metadata["score"], ...)
    #           for r in results]
    return SearchResponse(query=body.query, results=[], total=0)
