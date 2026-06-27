"""Admin user management — enriched with profile, consent, conversations & stats."""

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.middleware import get_admin_user
from src.api.db.database import get_users_collection, get_database
from src.api.services.auth_service import hash_password, serialize_user
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class AdminUserUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    verified: Optional[bool] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_oid(user_id: str) -> ObjectId:
    try:
        return ObjectId(user_id)
    except Exception:
        raise HTTPException(400, "Invalid user ID format")


def _get_or_404(user_id: str) -> dict:
    users = get_users_collection()
    user = users.find_one({"_id": _to_oid(user_id)})
    if not user:
        raise HTTPException(404, "User not found")
    return user


def _enrich_user(user: dict) -> dict:
    """Attach profile_mode, consent info, and aggregate counts to a user dict."""
    email = user.get("email")  # profiles/consent/conversations use email as user_id
    db = get_database()
    enriched = dict(user)

    # Profile info
    if db is not None and email:
        profile = db["profiles"].find_one({"user_id": email})
        enriched["has_profile"] = profile is not None
        enriched["profile_mode"] = (profile or {}).get("profile_mode", "general")

        consent = db["consent"].find_one({"user_id": email})
        enriched["has_consent"] = consent is not None
        enriched["research_data_consent"] = (consent or {}).get("research_data_consent", False)

        conv_count = db["conversations"].count_documents({"user_id": email})
        enriched["conversation_count"] = conv_count

        # Sum message_count across all user conversations
        pipeline = [
            {"$match": {"user_id": email}},
            {"$group": {"_id": None, "total": {"$sum": "$message_count"}}},
        ]
        result = list(db["conversations"].aggregate(pipeline))
        enriched["message_count"] = result[0]["total"] if result else 0

    return enriched


# ── CRUD ──────────────────────────────────────────────────────────────────────

@router.get("")
async def list_users(
    search: Optional[str] = Query(None, description="Filter by name or email (case-insensitive)"),
    _: dict = Depends(get_admin_user),
):
    users = get_users_collection()
    query = {}
    if search:
        import re
        pattern = re.compile(re.escape(search), re.IGNORECASE)
        query = {"$or": [{"name": pattern}, {"email": pattern}]}
    return [_enrich_user(serialize_user(u)) for u in users.find(query).sort("created_at", -1)]


@router.get("/stats")
async def get_user_stats(_: dict = Depends(get_admin_user)):
    """Aggregate user statistics across the platform."""
    users = get_users_collection()
    db = get_database()

    total = users.count_documents({})
    admins = users.count_documents({"role": "admin"})
    verified = users.count_documents({"verified": True})
    onboarding_completed = users.count_documents({"onboarding_completed": True})

    profiles_count = 0
    consent_granted = 0
    research_consent = 0
    full_mode = 0

    if db is not None:
        profiles_count = db["profiles"].count_documents({})
        full_mode = db["profiles"].count_documents({"profile_mode": "full"})
        consent_granted = db["consent"].count_documents({"has_consented": True})
        research_consent = db["consent"].count_documents({"research_data_consent": True})

    total_conv = db["conversations"].count_documents({}) if db is not None else 0
    total_msgs = db["messages"].count_documents({}) if db is not None else 0

    return {
        "total_users": total,
        "admin_users": admins,
        "verified_users": verified,
        "onboarding_completed": onboarding_completed,
        "users_with_profiles": profiles_count,
        "full_privacy_mode": full_mode,
        "consent_granted": consent_granted,
        "research_data_consent": research_consent,
        "total_conversations": total_conv,
        "total_messages": total_msgs,
    }


@router.get("/{user_id}")
async def get_user(user_id: str, _: dict = Depends(get_admin_user)):
    return _enrich_user(serialize_user(_get_or_404(user_id)))


@router.get("/{user_id}/profile")
async def get_user_profile(user_id: str, _: dict = Depends(get_admin_user)):
    """Get the user's demographic profile (respects privacy mode — only shows if consent allows)."""
    user = _get_or_404(user_id)
    email = user.get("email")
    db = get_database()
    if db is None:
        raise HTTPException(503, "Database not available")
    uid = email or user_id

    consent = db["consent"].find_one({"user_id": email}) if email else None
    profile = db["profiles"].find_one({"user_id": email}) if email else None
    if not profile:
        return {"user_id": uid, "has_profile": False, "profile_mode": "general", "data": None}

    # Respect privacy: show full data only if consent allows data sharing
    can_show = (consent or {}).get("research_data_consent", False) or (profile.get("profile_mode") == "general")

    return {
        "user_id": uid,
        "has_profile": True,
        "profile_mode": profile.get("profile_mode", "general"),
        "research_data_consent": (consent or {}).get("research_data_consent", False),
        "data": {
            "preferred_name": profile.get("preferred_name"),
            "age_range": profile.get("age_range") if can_show else None,
            "gender_identity": profile.get("gender_identity") if can_show else None,
            "pronouns": profile.get("pronouns") if can_show else None,
            "primary_language": profile.get("primary_language") if can_show else None,
            "disability": profile.get("disability") if can_show else None,
            "immigration_status": profile.get("immigration_status") if can_show else None,
            "indigenous_identity": profile.get("indigenous_identity") if can_show else None,
            "education_level": profile.get("education_level") if can_show else None,
            "literacy_comfort_ai": profile.get("literacy_comfort_ai") if can_show else None,
        },
        "redacted": not can_show,
    }


@router.get("/{user_id}/consent")
async def get_user_consent(user_id: str, _: dict = Depends(get_admin_user)):
    """Get the user's privacy consent preferences."""
    user = _get_or_404(user_id)
    email = user.get("email")
    db = get_database()
    if db is None:
        raise HTTPException(503, "Database not available")

    consent = db["consent"].find_one({"user_id": email}) if email else None
    if not consent:
        return {"user_id": user_id, "has_consented": False}

    return {
        "user_id": user_id,
        "has_consented": consent.get("has_consented", False),
        "profile_mode": consent.get("profile_mode", "general"),
        "research_data_consent": consent.get("research_data_consent", False),
        "consented_at": consent.get("consented_at"),
        "updated_at": consent.get("updated_at"),
    }


@router.get("/{user_id}/conversations")
async def get_user_conversations(
    user_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    _: dict = Depends(get_admin_user),
):
    """List the user's conversations and their messages (only if research consent is granted)."""
    user = _get_or_404(user_id)
    email = user.get("email")
    db = get_database()
    if db is None:
        raise HTTPException(503, "Database not available")

    consent = db["consent"].find_one({"user_id": email}) if email else None
    can_view = consent and consent.get("research_data_consent", False)

    if not can_view:
        raise HTTPException(403, "User has not granted research data consent — conversations are private.")

    cursor = db["conversations"].find({"user_id": email}) \
        .sort("updated_at", -1) \
        .skip((page - 1) * limit) \
        .limit(limit)
    items = []
    for conv in cursor:
        msg_count = db["messages"].count_documents(
            {"conversation_id": str(conv["_id"])}
        )
        items.append({
            "id": str(conv["_id"]),
            "title": conv.get("title", "Untitled"),
            "profile_key": conv.get("profile_key"),
            "message_count": msg_count,
            "created_at": conv.get("created_at"),
            "updated_at": conv.get("updated_at"),
        })

    total = db["conversations"].count_documents({"user_id": email})
    return {"conversations": items, "total": total, "page": page, "limit": limit}


@router.get("/{user_id}/activity")
async def get_user_activity(user_id: str, _: dict = Depends(get_admin_user)):
    """Get aggregate activity statistics for a single user."""
    user = _get_or_404(user_id)
    email = user.get("email")
    db = get_database()
    if db is None:
        raise HTTPException(503, "Database not available")

    if not email:
        return {"conversation_count": 0, "message_count": 0, "last_conversation_at": None, "last_message_at": None}

    conv_count = db["conversations"].count_documents({"user_id": email})

    # Sum message_count from all user's conversations
    pipeline = [
        {"$match": {"user_id": email}},
        {"$group": {"_id": None, "total": {"$sum": "$message_count"}}},
    ]
    result = list(db["conversations"].aggregate(pipeline))
    msg_count = result[0]["total"] if result else 0

    # Last activity dates
    last_conv = db["conversations"].find_one(
        {"user_id": email}, sort=[("updated_at", -1)]
    )
    last_message = db["messages"].find_one(
        {"conversation_id": {"$regex": f"^{str(last_conv["_id"])}"}}, sort=[("created_at", -1)]
    ) if last_conv else None

    return {
        "conversation_count": conv_count,
        "message_count": msg_count,
        "last_conversation_at": (last_conv or {}).get("updated_at"),
        "last_message_at": (last_message or {}).get("created_at"),
    }


@router.patch("/{user_id}")
async def update_user(
    user_id: str,
    body: AdminUserUpdate,
    _: dict = Depends(get_admin_user),
):
    _get_or_404(user_id)
    fields: dict = {}
    if body.name is not None:
        fields["name"] = body.name
    if body.password is not None:
        fields["hashed_password"] = hash_password(body.password)
    if body.role is not None:
        if body.role not in ("user", "admin"):
            raise HTTPException(400, "role must be 'user' or 'admin'")
        fields["role"] = body.role
    if body.verified is not None:
        fields["verified"] = body.verified
    if not fields:
        raise HTTPException(400, "Nothing to update")

    users = get_users_collection()
    oid = _to_oid(user_id)
    users.update_one({"_id": oid}, {"$set": fields})
    return _enrich_user(serialize_user(users.find_one({"_id": oid})))


@router.delete("/{user_id}", status_code=200)
async def delete_user(user_id: str, _: dict = Depends(get_admin_user)):
    """Delete a user and all associated data (profile, consent, conversations, messages)."""
    user = _get_or_404(user_id)
    email = user.get("email")
    db = get_database()
    if db is None:
        raise HTTPException(503, "Database not available")

    # Remove all user data across collections
    users = get_users_collection()
    oid = _to_oid(user_id)
    users.delete_one({"_id": oid})

    if email:
        db["profiles"].delete_one({"user_id": email})
        db["consent"].delete_one({"user_id": email})

        # Conversations and messages
        conv_ids = [
            str(c["_id"])
            for c in db["conversations"].find({"user_id": email}, {"_id": 1})
        ]
        if conv_ids:
            db["messages"].delete_many({"conversation_id": {"$in": conv_ids}})
        db["conversations"].delete_many({"user_id": email})

    return {"message": "User and all associated data deleted"}
