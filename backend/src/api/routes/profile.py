"""
routes/profile.py — User profile & consent endpoints
=======================================================
Endpoints:
    GET    /api/v1/profile          — Get demographics
    PUT    /api/v1/profile          — Create or update demographics
    GET    /api/v1/profile/consent  — Get consent preferences
    PUT    /api/v1/profile/consent  — Update consent preferences
    POST   /api/v1/profile/onboarding/complete  — Finish onboarding
    DELETE /api/v1/profile/data     — Delete user data (GDPR)
"""

from fastapi import APIRouter, Depends
from src.api.schemas.profile import (
    ProfileResponse,
    ProfileUpdateRequest,
    ConsentResponse,
    ConsentUpdateRequest,
)
from src.api.middleware import require_current_user
from src.api.db.models import User
from src.api.services.user_service import UserService

router = APIRouter()


@router.get("", response_model=ProfileResponse)
async def get_profile(user: User = Depends(require_current_user)):
    """
    Get the current user's demographic profile.

    Returns a default/empty profile if onboarding hasn't been completed yet.
    """
    # TODO: Implement
    # service = UserService(user.id)
    # profile = await service.get_profile()
    # if not profile:
    #     raise HTTPException(404, "Profile not found — complete onboarding first.")
    # return ProfileResponse(...)
    raise NotImplementedError("TODO: implement get_profile")


@router.put("", response_model=ProfileResponse)
async def update_profile(
    body: ProfileUpdateRequest,
    user: User = Depends(require_current_user),
):
    """
    Create or update the user's demographic profile.

    If no profile exists yet, one is created.  Otherwise, the provided
    fields are merged into the existing profile (partial update).
    """
    # TODO: Implement
    raise NotImplementedError("TODO: implement update_profile")


@router.get("/consent", response_model=ConsentResponse)
async def get_consent(user: User = Depends(require_current_user)):
    """
    Get the user's current consent and privacy preferences.
    """
    # TODO: Implement
    raise NotImplementedError("TODO: implement get_consent")


@router.put("/consent", response_model=ConsentResponse)
async def update_consent(
    body: ConsentUpdateRequest,
    user: User = Depends(require_current_user),
):
    """
    Update privacy mode and/or research data consent.

    Switching from 'full' to 'general' mode should anonymise
    the user's profile data.
    """
    # TODO: Implement
    raise NotImplementedError("TODO: implement update_consent")


@router.post("/onboarding/complete")
async def complete_onboarding(user: User = Depends(require_current_user)):
    """
    Mark the onboarding flow as complete.

    Called after the user has submitted consent + profile.
    Sets ``onboarding_completed = True`` on the user account.
    """
    # TODO: Implement
    raise NotImplementedError("TODO: implement complete_onboarding")


@router.delete("/data")
async def delete_user_data(user: User = Depends(require_current_user)):
    """
    Delete all user data (profile, consent, conversations, messages).

    This is a GDPR / privacy compliance endpoint
    ("right to be forgotten").
    """
    # TODO: Implement
    raise NotImplementedError("TODO: implement delete_user_data")
