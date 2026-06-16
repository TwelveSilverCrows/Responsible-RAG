"""Chat routes — conversations, messages, and RAG with MongoDB persistence."""

from uuid import uuid4
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from bson.objectid import ObjectId

from src.api.schemas.chat import (
    ChatRequest, ChatResponse, CitationSchema,
    ConversationListItem, ConversationListResponse, ConversationResponse,
    MessageResponse, CreateConversationRequest, RenameConversationRequest,
)
from src.api.middleware import get_current_user
from src.api.deps import get_rag_chain
from src.api.db.database import get_users_collection
from src.core.profiles import RAGPopulation
from src.core.rag_chain import RAGChain

router = APIRouter()


def _get_db():
    from src.api.db.database import get_database
    return get_database()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _conv_to_response(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "title": doc.get("title", "New conversation"),
        "profile_key": doc.get("profile_key"),
        "messages": [],
        "message_count": doc.get("message_count", 0),
        "created_at": doc.get("created_at", ""),
        "updated_at": doc.get("updated_at", ""),
    }


def _conv_list_item(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "title": doc.get("title", "New conversation"),
        "last_message": doc.get("last_message"),
        "last_message_at": doc.get("last_message_at"),
        "created_at": doc.get("created_at", ""),
        "message_count": doc.get("message_count", 0),
    }


def _msg_to_response(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "conversation_id": doc.get("conversation_id", ""),
        "role": doc.get("role", "user"),
        "content": doc.get("content", ""),
        "citations": doc.get("citations", []),
        "is_streaming": doc.get("is_streaming", False),
        "created_at": doc.get("created_at", ""),
    }


# ── Conversations ─────────────────────────────────────────────────────────────

@router.get("/conversations")
async def list_conversations(
    page: int = 1,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
):
    db = _get_db()
    if db is None:
        raise HTTPException(503, "Database not available")

    user_id = current_user["sub"]
    cursor = db["conversations"].find({"user_id": user_id}) \
        .sort("updated_at", -1) \
        .skip((page - 1) * limit) \
        .limit(limit)
    items = [_conv_list_item(c) for c in cursor]
    total = db["conversations"].count_documents({"user_id": user_id})
    return {"conversations": items, "total": total, "page": page, "limit": limit}


@router.post("/conversations", status_code=201)
async def create_conversation(
    body: CreateConversationRequest,
    current_user: dict = Depends(get_current_user),
):
    db = _get_db()
    if db is None:
        raise HTTPException(503, "Database not available")

    now = _now()
    doc = {
        "user_id": current_user["sub"],
        "title": body.title or "New conversation",
        "profile_key": body.profile_key,
        "message_count": 0,
        "last_message": None,
        "last_message_at": None,
        "created_at": now,
        "updated_at": now,
    }
    result = db["conversations"].insert_one(doc)
    doc["_id"] = result.inserted_id
    return _conv_to_response(doc)


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
):
    db = _get_db()
    if db is None:
        raise HTTPException(503, "Database not available")

    conv = db["conversations"].find_one({"_id": ObjectId(conversation_id), "user_id": current_user["sub"]})
    if not conv:
        raise HTTPException(404, "Conversation not found")

    messages = list(db["messages"].find({"conversation_id": conversation_id}).sort("created_at", 1))
    resp = _conv_to_response(conv)
    resp["messages"] = [_msg_to_response(m) for m in messages]
    return resp


@router.put("/conversations/{conversation_id}")
async def rename_conversation(
    conversation_id: str,
    body: RenameConversationRequest,
    current_user: dict = Depends(get_current_user),
):
    db = _get_db()
    if db is None:
        raise HTTPException(503, "Database not available")

    result = db["conversations"].update_one(
        {"_id": ObjectId(conversation_id), "user_id": current_user["sub"]},
        {"$set": {"title": body.title, "updated_at": _now()}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Conversation not found")

    conv = db["conversations"].find_one({"_id": ObjectId(conversation_id)})
    return _conv_to_response(conv)


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
):
    db = _get_db()
    if db is None:
        raise HTTPException(503, "Database not available")

    result = db["conversations"].delete_one(
        {"_id": ObjectId(conversation_id), "user_id": current_user["sub"]}
    )
    if result.deleted_count == 0:
        raise HTTPException(404, "Conversation not found")
    db["messages"].delete_many({"conversation_id": conversation_id})
    return {"status": "ok"}


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    page: int = 1,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
):
    db = _get_db()
    if db is None:
        raise HTTPException(503, "Database not available")

    conv = db["conversations"].find_one({"_id": ObjectId(conversation_id), "user_id": current_user["sub"]})
    if not conv:
        raise HTTPException(404, "Conversation not found")

    cursor = db["messages"].find({"conversation_id": conversation_id}) \
        .sort("created_at", 1) \
        .skip((page - 1) * limit) \
        .limit(limit)
    return [_msg_to_response(m) for m in cursor]


# ── RAG (single-turn) ────────────────────────────────────────────────────────

@router.post("")
async def chat(
    body: ChatRequest,
    chain: RAGChain = Depends(get_rag_chain),
    current_user: dict = Depends(get_current_user),
):
    db = _get_db()

    # Resolve profile
    group_prompt = _resolve_profile(body.profile_key)

    # Get or create conversation
    conv_id = body.conversation_id
    user_id = current_user["sub"]
    now = _now()

    if not conv_id:
        conv_doc = {
            "user_id": user_id,
            "title": body.question[:80] + ("..." if len(body.question) > 80 else ""),
            "profile_key": body.profile_key,
            "message_count": 0,
            "last_message": None,
            "last_message_at": None,
            "created_at": now,
            "updated_at": now,
        }
        if db is not None:
            result = db["conversations"].insert_one(conv_doc)
            conv_id = str(result.inserted_id)
        else:
            conv_id = f"conv-{uuid4().hex[:12]}"

    # Store user message
    msg_id = f"msg-{uuid4().hex[:12]}"
    if db is not None:
        db["messages"].insert_one({
            "conversation_id": conv_id,
            "role": "user",
            "content": body.question,
            "citations": [],
            "is_streaming": False,
            "created_at": now,
        })

    # Invoke RAG
    result = chain.invoke(body.question, group_prompt)

    citations = [
        CitationSchema(
            id=f"cit-{i}",
            source_id=src.get("source_id", ""),
            source_title=src.get("source_title", "Unknown source"),
            source_type=src.get("source_type", "pdf"),
            authors=src.get("authors", []),
            publication_date=src.get("publication_date"),
            publisher=src.get("publisher"),
            url=src.get("url", ""),
            doi=src.get("doi", ""),
            language=src.get("language"),
            description=src.get("description"),
            tags=src.get("tags", []),
            content_sensitivity=src.get("content_sensitivity", "low"),
            excerpt=src.get("excerpt", ""),
            number=i + 1,
        )
        for i, src in enumerate(result.sources)
    ]

    # Store assistant message
    if db is not None:
        db["messages"].insert_one({
            "conversation_id": conv_id,
            "role": "assistant",
            "content": result.answer,
            "citations": [c.model_dump() for c in citations],
            "is_streaming": False,
            "created_at": _now(),
        })
        db["conversations"].update_one(
            {"_id": ObjectId(conv_id) if ObjectId.is_valid(conv_id) else conv_id},
            {"$set": {
                "last_message": result.answer[:100],
                "last_message_at": _now(),
                "updated_at": _now(),
            }, "$inc": {"message_count": 2}},
        )

    return ChatResponse(
        answer=result.answer,
        sources=citations,
        conversation_id=conv_id,
        message_id=msg_id,
        profile_key=body.profile_key,
    )


# ── Profile resolver ──────────────────────────────────────────────────────────

_PROFILE_KEY_MAP: dict[str, str] = {
    "general": "GENERAL",
    "senior": "SENIOR_LOW_EDU_CANADA",
    "lgbt_teen": "LGBT_CANADIAN_TEEN",
    "lgbt": "LGBT_CANADIAN_TEEN",
    "indigenous": "INDIGENOUS_COMMUNITY_LEADER_CA",
    "disabled": "MIDAGED_DISABLED_CANADIAN",
    "full": "SENIOR_LOW_EDU_CANADA",
}


def _resolve_profile(profile_key: str | None) -> str:
    if not profile_key:
        return RAGPopulation.GENERAL.value
    key = profile_key.strip().lower()
    member_name = _PROFILE_KEY_MAP.get(key)
    if not member_name:
        return RAGPopulation.GENERAL.value
    try:
        return RAGPopulation[member_name].value
    except KeyError:
        return RAGPopulation.GENERAL.value


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
