"""
routes/chat.py — Chat endpoints
=================================
Core RAG conversation endpoints. Supports both single-turn and streaming
responses.

Endpoints:
    GET    /api/v1/chat/conversations       — List user's conversations
    POST   /api/v1/chat/conversations       — Create new conversation
    GET    /api/v1/chat/conversations/{id}  — Get conversation with messages
    PUT    /api/v1/chat/conversations/{id}  — Rename conversation
    DELETE /api/v1/chat/conversations/{id}  — Delete conversation
    GET    /api/v1/chat/conversations/{id}/messages  — Get messages
    POST   /api/v1/chat                     — Single-turn RAG answer
    POST   /api/v1/chat/stream              — Streaming RAG answer (SSE)

Low-memory notes:
    - Use streaming for long responses — avoids buffering the full answer.
    - RAG chain is loaded lazily and cached (singleton) across requests.
    - Conversations are paginated — never load all history.
"""

from uuid import uuid4

from fastapi import APIRouter, Depends
from src.api.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatStreamRequest,
    CitationSchema,
    ConversationResponse,
    ConversationListItem,
    ConversationListResponse,
    MessageResponse,
    CreateConversationRequest,
    RenameConversationRequest,
)
from src.api.middleware import require_current_user
from src.api.deps import get_rag_chain
from src.api.db.models import User
from src.core.config import Settings
from src.core.profiles import RAGPopulation
from src.core.rag_chain import RAGChain

router = APIRouter()


# ── Conversations ─────────────────────────────────────────────────────────────

@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    page: int = 1,
    limit: int = 20,
    user: User = Depends(require_current_user),
):
    """
    List the current user's conversations, most recent first.

    Paginated with ``page`` and ``limit`` query parameters.
    """
    # TODO: Implement
    # service = ChatService(user.id)
    # convos, total = await service.list_conversations(page=page, limit=limit)
    # items = [ConversationListItem.model_validate(c) for c in convos]
    # return ConversationListResponse(conversations=items, total=total, page=page, limit=limit)
    return ConversationListResponse(
        conversations=[], total=0, page=page, limit=limit,
    )


@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    body: CreateConversationRequest,
    user: User = Depends(require_current_user),
):
    """
    Start a new conversation.

    Optionally provide a title and audience profile key.
    """
    # TODO: Implement
    raise NotImplementedError("TODO: implement create_conversation")


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    user: User = Depends(require_current_user),
):
    """
    Get a full conversation including all messages.
    """
    # TODO: Implement
    raise NotImplementedError("TODO: implement get_conversation")


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def rename_conversation(
    conversation_id: str,
    body: RenameConversationRequest,
    user: User = Depends(require_current_user),
):
    """
    Rename a conversation.
    """
    # TODO: Implement
    raise NotImplementedError("TODO: implement rename_conversation")


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user: User = Depends(require_current_user),
):
    """
    Delete a conversation and all its messages.
    """
    # TODO: Implement
    raise NotImplementedError("TODO: implement delete_conversation")


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
async def get_messages(
    conversation_id: str,
    page: int = 1,
    limit: int = 50,
    user: User = Depends(require_current_user),
):
    """
    Get paginated messages for a conversation, oldest first.
    """
    # TODO: Implement
    raise NotImplementedError("TODO: implement get_messages")


# ── RAG (single-turn) ────────────────────────────────────────────────────────

@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    chain: RAGChain = Depends(get_rag_chain),
):
    """
    Single-turn Q&A with the RAG pipeline.

    Accepts a question and optional audience profile.
    Returns the generated answer with source citations.
    Uses the general profile by default (no login required).
    """
    # Resolve profile key → RAGPopulation prompt text (defaults to GENERAL)
    group_prompt = _resolve_profile(body.profile_key)

    # Invoke the RAG pipeline
    result = chain.invoke(body.question, group_prompt)

    # Build citation list from source titles
    citations = [
        CitationSchema(
            id=f"cit-{i}",
            source_id=title,
            excerpt="",               # full excerpt requires chunk access
            number=i + 1,
        )
        for i, title in enumerate(result.sources)
    ]

    return ChatResponse(
        answer=result.answer,
        sources=citations,
        conversation_id=body.conversation_id or "dev-conv-id",
        message_id=f"msg-{uuid4().hex[:12]}",
        profile_key=body.profile_key,
    )


@router.post("/stream")
async def chat_stream(
    body: ChatStreamRequest,
    chain: RAGChain = Depends(get_rag_chain),
    user: User = Depends(require_current_user),
):
    """
    Streaming Q&A — returns a Server-Sent Events (SSE) stream.

    Each chunk is a JSON line.  The final chunk contains ``"done": true``
    and the full source list.

    Example (JavaScript):
        const stream = await fetch("/api/v1/chat/stream", { ... });
        const reader = stream.body.getReader();
    """
    # TODO: Implement using StreamingResponse
    # from fastapi.responses import StreamingResponse
    # async def event_stream():
    #     service = ChatService(user.id)
    #     async for chunk in service.ask_rag_stream(body.question, body.conversation_id, body.profile_key):
    #         yield json.dumps(chunk) + "\\n"
    # return StreamingResponse(event_stream(), media_type="text/event-stream")
    return {"detail": "Streaming not yet implemented"}


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

# Mapping from short UI keys → RAGPopulation member names
_PROFILE_KEY_MAP: dict[str, str] = {
    "general": "GENERAL",
    "senior": "SENIOR_LOW_EDU_CANADA",
    "lgbt_teen": "LGBT_CANADIAN_TEEN",
    "lgbt": "LGBT_CANADIAN_TEEN",
    "indigenous": "INDIGENOUS_COMMUNITY_LEADER_CA",
    "disabled": "MIDAGED_DISABLED_CANADIAN",
    "full": "SENIOR_LOW_EDU_CANADA",       # fallback for "full" privacy mode
}


def _resolve_profile(profile_key: str | None) -> str:
    """
    Convert a short UI profile key (e.g. ``"senior"``) into the full
    RAGPopulation prompt text.

    Defaults to the GENERAL profile when no key is provided or the key
    is unknown — no login required.
    """
    if not profile_key:
        return RAGPopulation.GENERAL.value

    # Normalise: lowercase, strip whitespace
    key = profile_key.strip().lower()

    # Look up the enum member name
    member_name = _PROFILE_KEY_MAP.get(key)
    if not member_name:
        return RAGPopulation.GENERAL.value

    try:
        return RAGPopulation[member_name].value
    except KeyError:
        return RAGPopulation.GENERAL.value
