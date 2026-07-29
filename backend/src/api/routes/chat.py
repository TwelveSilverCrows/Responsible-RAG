"""Chat routes — conversations, messages, and RAG with MongoDB persistence."""

from uuid import uuid4
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from bson.objectid import ObjectId

from src.api.schemas.chat import (
    ChatRequest, ChatResponse, CitationSchema, CreateConversationRequest, RenameConversationRequest,
)
from src.api.middleware import get_current_user
from src.api.deps import get_rag_chain, get_profile_generator

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

############ Helper functions for chat memory
def _init_memory_doc(now: str) -> dict:
    return {
        "enabled": True,
        "summary": "",
        "facts": [],
        "recent_turns": [],
        "last_refreshed_at": now,
        "last_refreshed_turn_count": 0,
    }

def _fetch_recent_turns(db, conversation_id: str, limit: int = 5) -> list[dict]:
    """Fetch the most recent turns (user + assistant messages) for a conversation."""
    cursor = db["messages"].find({"conversation_id": conversation_id})
    cursor = cursor.sort("created_at", -1).limit(limit * 2)  # Fetch more to account for both roles
    turns = [{"role": m["role"], "content": m["content"], "created_at": m["created_at"]} for m in cursor]
    return list (reversed(turns))  # Return in chronological order, turns is a stack of messages, so we reverse it to get the correct order

def _build_memory_context(memory:dict, recent_turns: list[dict])-> str:
    """Build a context string from the memory summary, facts, and recent turns."""
    if not memory or not memory.get("enabled", True):
        return ""

    summary = memory.get("summary", "").strip()
    facts = memory.get("facts", [])
    recent_turns_text = "\n".join(
        f"{turn['role'].title()}: {turn['content']}"
        for turn in recent_turns
    )
    pieces = []
    if summary:
        pieces.append(f"Summary of conversation so far:\n{summary}")
    if facts:
        pieces.append(f"Facts:\n" + "\n".join(f"- {fact}" for fact in facts))
    if recent_turns_text:
        pieces.append(f"Recent conversation:\n" + recent_turns_text)

    return "\n\n".join(pieces)

def _extract_memory_facts(memory: dict, user_question: str, assistant_answer: str) -> list[str]:
    # Minimal first version: keep previous facts, add any new obvious fact
    memory_facts = memory.get("facts", [])
    #TODO: Implement a more sophisticated fact extraction from the user question and assistant answer
    return memory_facts

def _update_memory(memory:dict, user_question:str, assistant_answer:str, recent_turns:list[dict], now:str) -> dict:
    """Update the memory document with new summary, facts, and recent turns."""
    # Extract facts from the user question and assistant answer
    new_facts = _extract_memory_facts(memory, user_question, assistant_answer)
    updated_facts = list(set(memory.get("facts", []) + new_facts))  # Deduplicate to conserve memory

    # Update recent turns
    updated_recent_turns = recent_turns[-10:]  # Keep only the last 10 turns

    # Update summary 
    #TODO: Implement a more sophisticated summary update, possibly using an LLM to summarise the conversation so far
    if memory.get("summary"):
        updated_summary = memory.get("summary", "") + f"\nUser: {user_question}\nAssistant: {assistant_answer}"
    else:
        updated_summary = f"User: {user_question}\nAssistant: {assistant_answer}" # have to set the summary to something to break out of the empty state

    return {
        "enabled": memory.get("enabled", True),
        "summary": updated_summary.strip(),
        "facts": updated_facts,
        "recent_turns": updated_recent_turns,
        "last_refreshed_at": now,
        "last_refreshed_turn_count": len(updated_recent_turns),
    }


###############


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
    chain = Depends(get_rag_chain),
    generator = Depends(get_profile_generator),
    current_user: dict = Depends(get_current_user),
):
    db = _get_db()

    # Build personalised profile prompt from stored user profile
    group_prompt = _build_profile_prompt(db, generator, current_user, body.question)

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
            # Initialising memory structure for the conversation
            "memory": {
                _init_memory_doc(now)
            },
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

    #Build memory before invoking
    conv_memory  = conv_doc.get("memory") or _init_memory_doc(now) #failsafe
    recent_turns = _fetch_recent_turns(db, conv_id, limit=5) if db is not None else []
    memory_context = _build_memory_context(conv_memory, recent_turns)

    # Invoke RAG
    result = chain.invoke(body.question, group_prompt, memory_context)

    citations = [_con
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


# ── Profile prompt builder ───────────────────────────────────────────────────

_DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful, polite AI assistant. Answer the user's question "
    "concisely and clearly. Be respectful and direct."
)


_AGE_MAP: dict[str, str] = {
    "under_18": "Youth (under 18)",
    "18_30": "Young adult (18–30 years)",
    "31_50": "Adult (31–50 years)",
    "51_65": "Middle-aged adult (51–65 years)",
    "65_plus": "Senior (65+ years)",
    "prefer_not_to_say": "Adult",
}

_EDU_MAP: dict[str, str] = {
    "no_formal": "No formal education",
    "high_school": "High school diploma",
    "some_college": "Some post-secondary education",
    "bachelors": "Bachelor's degree",
    "masters": "Master's degree",
    "doctoral": "Doctoral degree",
}

_IMM_MAP: dict[str, str] = {
    "citizen": "Canadian citizen",
    "permanent_resident": "Permanent resident",
    "temporary_resident": "Temporary resident / Visa holder",
    "refugee": "Refugee / Protected person",
    "undocumented": "Undocumented / No legal status",
}

_INDIG_MAP: dict[str, str] = {
    "first_nations": "First Nations",
    "metis": "Métis",
    "inuit": "Inuit",
    "non_indigenous": "Non-Indigenous",
}


def _map_profile_to_generation(profile_doc: dict) -> dict[str, str]:
    """Map stored profile fields to the format expected by ProfileAugmenter."""
    mapped: dict[str, str] = {}

    age = profile_doc.get("age_range")
    if age and age in _AGE_MAP:
        mapped["age_group"] = _AGE_MAP[age]

    gender_ids = profile_doc.get("gender_identity", [])
    if gender_ids:
        mapped["gender"] = ", ".join(
            g.replace("_", " ").title() for g in gender_ids if g
        )

    lang = profile_doc.get("primary_language")
    if lang:
        mapped["primary_language"] = lang

    edu = profile_doc.get("education_level")
    if edu and edu in _EDU_MAP:
        mapped["education_level"] = _EDU_MAP[edu]

    imm = profile_doc.get("immigration_status")
    if imm and imm in _IMM_MAP:
        mapped["citizen_status"] = _IMM_MAP[imm]

    indig = profile_doc.get("indigenous_identity")
    if indig and indig in _INDIG_MAP:
        mapped["indigenous_status"] = _INDIG_MAP[indig]

    disabilities = profile_doc.get("disability", [])
    if disabilities and "none" not in disabilities:
        mapped["disability_status"] = ", ".join(
            d.replace("_", " ").title() for d in disabilities
        )
    elif disabilities and "none" in disabilities:
        mapped["disability_status"] = "No disclosed disability"

    return mapped


def _build_profile_prompt(
    db, generator, current_user: dict, query: str,
) -> str:
    """
    Build a personalised system prompt from the user's stored demographic profile.

    Falls back to a simple default when no profile exists or the user
    has opted for 'general' privacy mode.
    """
    if db is None:
        return _DEFAULT_SYSTEM_PROMPT

    profile_doc = db["profiles"].find_one({"user_id": current_user["sub"]})
    if not profile_doc:
        return _DEFAULT_SYSTEM_PROMPT

    # If the user chose 'general' privacy mode, don't personalise
    if profile_doc.get("profile_mode") == "general":
        return _DEFAULT_SYSTEM_PROMPT

    user_profile = _map_profile_to_generation(profile_doc)
    if not user_profile:
        return _DEFAULT_SYSTEM_PROMPT

    return generator.generate_prompt(
        user_profile=user_profile,
        user_query=query,
    )


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

