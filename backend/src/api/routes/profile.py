"""Profile & consent endpoints — stores user demographics and privacy choices."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from src.api.schemas.profile import ProfileUpdateRequest, ConsentUpdateRequest
from src.api.middleware import get_current_user
from src.api.db.database import get_users_collection

router = APIRouter()


def _get_profiles_collection():
    from src.api.db.database import get_database
    db = get_database()
    if db is None:
        return None
    return db["profiles"]


def _get_consent_collection():
    from src.api.db.database import get_database
    db = get_database()
    if db is None:
        return None
    return db["consent"]


# ── Profile ───────────────────────────────────────────────────────────────────

def _profile_to_response(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "user_id": doc["user_id"],
        "preferred_name": doc.get("preferred_name", ""),
        "age_range": doc.get("age_range"),
        "gender_identity": doc.get("gender_identity", []),
        "pronouns": doc.get("pronouns"),
        "primary_language": doc.get("primary_language"),
        "disability": doc.get("disability", []),
        "immigration_status": doc.get("immigration_status"),
        "indigenous_identity": doc.get("indigenous_identity"),
        "education_level": doc.get("education_level"),
        "literacy_comfort_ai": doc.get("literacy_comfort_ai"),
        "profile_mode": doc.get("profile_mode", "general"),
        "created_at": doc.get("created_at", ""),
        "updated_at": doc.get("updated_at", ""),
    }


@router.get("")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get the current user's demographic profile."""
    profiles = _get_profiles_collection()
    if profiles is None:
        raise HTTPException(503, "Database not available")
    doc = profiles.find_one({"user_id": current_user["sub"]})
    if not doc:
        raise HTTPException(404, "No profile found. Complete onboarding first.")
    return _profile_to_response(doc)


@router.put("")
async def update_profile(
    body: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Create or update the user's demographic profile."""
    profiles = _get_profiles_collection()
    if profiles is None:
        raise HTTPException(503, "Database not available")

    data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(400, "No fields to update")

    now = datetime.now(timezone.utc).isoformat()
    existing = profiles.find_one({"user_id": current_user["sub"]})

    if existing:
        data["updated_at"] = now
        profiles.update_one({"user_id": current_user["sub"]}, {"$set": data})
    else:
        data["user_id"] = current_user["sub"]
        data["created_at"] = now
        data["updated_at"] = now
        profiles.insert_one(data)

    doc = profiles.find_one({"user_id": current_user["sub"]})
    return _profile_to_response(doc)


# ── Consent ───────────────────────────────────────────────────────────────────

def _consent_to_response(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "user_id": doc["user_id"],
        "profile_mode": doc.get("profile_mode", "general"),
        "research_data_consent": doc.get("research_data_consent", False),
        "has_consented": doc.get("has_consented", False),
        "consented_at": doc.get("consented_at"),
        "updated_at": doc.get("updated_at"),
    }


@router.get("/consent")
async def get_consent(current_user: dict = Depends(get_current_user)):
    """Get the user's consent and privacy preferences."""
    consent = _get_consent_collection()
    if consent is None:
        raise HTTPException(503, "Database not available")
    doc = consent.find_one({"user_id": current_user["sub"]})
    if not doc:
        raise HTTPException(404, "No consent record found.")
    return _consent_to_response(doc)


@router.put("/consent")
async def update_consent(
    body: ConsentUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Create or update consent preferences."""
    consent_coll = _get_consent_collection()
    if consent_coll is None:
        raise HTTPException(503, "Database not available")

    data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(400, "No fields to update")

    now = datetime.now(timezone.utc).isoformat()
    existing = consent_coll.find_one({"user_id": current_user["sub"]})

    if existing:
        data["updated_at"] = now
        consent_coll.update_one({"user_id": current_user["sub"]}, {"$set": data})
    else:
        data["user_id"] = current_user["sub"]
        data["has_consented"] = True
        data["consented_at"] = now
        data["updated_at"] = now
        consent_coll.insert_one(data)

    doc = consent_coll.find_one({"user_id": current_user["sub"]})
    return _consent_to_response(doc)


@router.post("/onboarding/complete")
async def complete_onboarding(current_user: dict = Depends(get_current_user)):
    """Mark onboarding as complete — sets onboarding_completed=True on the user."""
    users = get_users_collection()
    if users is None:
        raise HTTPException(503, "Database not available")
    result = users.update_one(
        {"email": current_user["sub"]},
        {"$set": {"onboarding_completed": True}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "User not found")
    return {"status": "ok"}


@router.delete("/data")
async def delete_user_data(current_user: dict = Depends(get_current_user)):
    """Delete all user data (profile, consent) — GDPR right to be forgotten."""
    from src.api.db.database import get_database
    db = get_database()
    if db is None:
        raise HTTPException(503, "Database not available")
    email = current_user["sub"]
    db["profiles"].delete_many({"user_id": email})
    db["consent"].delete_many({"user_id": email})
    db["conversations"].delete_many({"user_id": email})
    db["messages"].delete_many({"user_id": email})
    return {"message": "All user data deleted"}
