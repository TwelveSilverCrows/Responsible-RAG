"""
services/user_service.py — User profile & consent management
==============================================================
Handles demographics CRUD, consent preferences, profile mode switching,
and the onboarding flow.

Relationships (MongoDB collections):
    users (User) 1:1 profiles (UserProfile)   — demographics
    users (User) 1:1 consent (ConsentRecord)  — consent/preferences
"""

from typing import Optional
from src.api.db.models import UserProfile, ConsentRecord


class UserService:
    """
    Profile and consent operations for a given user.

    Usage:
        service = UserService(user_id)
        profile = await service.get_profile()
        await service.update_profile({"preferred_name": "Alex"})
    """

    def __init__(self, user_id: str):
        self.user_id = user_id

    # ── Profile ───────────────────────────────────────────────────────────────

    async def get_profile(self) -> Optional[UserProfile]:
        """
        Get the user's demographic profile.

        Returns None if no profile has been created yet (new user).
        """
        # TODO: Implement
        # return await profiles_repo.find_one({"user_id": self.user_id})
        raise NotImplementedError("TODO: implement get_profile")

    async def create_profile(self, data: dict) -> UserProfile:
        """
        Create a new demographic profile (during onboarding).

        ``data`` should match ProfileUpdateRequest fields.
        """
        # TODO: Implement
        # profile = UserProfile(user_id=self.user_id, **data)
        # await profiles_repo.insert_one(profile)
        # return profile
        raise NotImplementedError("TODO: implement create_profile")

    async def update_profile(self, data: dict) -> Optional[UserProfile]:
        """
        Partial update to the user's profile.

        Only the fields present in ``data`` are updated (MongoDB ``$set``).
        """
        # TODO: Implement
        raise NotImplementedError("TODO: implement update_profile")

    # ── Consent ───────────────────────────────────────────────────────────────

    async def get_consent(self) -> Optional[ConsentRecord]:
        """Get the user's current consent preferences."""
        # TODO: Implement
        raise NotImplementedError("TODO: implement get_consent")

    async def create_consent(self, data: dict) -> ConsentRecord:
        """
        Create consent record (during onboarding).

        ``data`` should contain ``profile_mode`` and ``research_data_consent``.
        """
        # TODO: Implement
        raise NotImplementedError("TODO: implement create_consent")

    async def update_consent(self, data: dict) -> Optional[ConsentRecord]:
        """Update consent preferences."""
        # TODO: Implement
        raise NotImplementedError("TODO: implement update_consent")

    # ── Onboarding ────────────────────────────────────────────────────────────

    async def complete_onboarding(self) -> bool:
        """
        Mark the user's onboarding as complete.

        Sets ``onboarding_completed = True`` on the User document and
        ``has_consented = True`` on the Consent record.
        """
        # TODO: Implement
        raise NotImplementedError("TODO: implement complete_onboarding")

    async def delete_user_data(self) -> bool:
        """
        Delete the user's profile, consent, conversations, and messages.
        (GDPR / privacy — "right to be forgotten.")

        Does NOT delete the User account itself.
        """
        # TODO: Implement
        raise NotImplementedError("TODO: implement delete_user_data")
