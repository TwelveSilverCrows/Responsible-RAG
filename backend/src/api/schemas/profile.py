"""
schemas/profile.py — User profile & consent
=============================================
Handles demographics collection (onboarding) and privacy consent preferences.
Matches the frontend's UserProfile and ConsentRecord interfaces.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ── Enums mirroring frontend types ────────────────────────────────────────────

ProfileMode = str  # "full" | "general"

AgeRange = Optional[str]
# "under_18" | "18_30" | "31_50" | "51_65" | "65_plus" | "prefer_not_to_say"

DisabilityType = Optional[list[str]]
# "visual" | "hearing" | "cognitive" | "mobility" | "mental_health" | "none"

ImmigrationStatus = Optional[str]
# "citizen" | "permanent_resident" | "temporary_resident" | "refugee" | "undocumented"

IndigenousIdentity = Optional[str]
# "first_nations" | "metis" | "inuit" | "non_indigenous"

EducationLevel = Optional[str]
# "no_formal" | "high_school" | "some_college" | "bachelors" | "masters" | "doctoral"


# ═══════════════════════════════════════════════════════════════════════════════
# Profile
# ═══════════════════════════════════════════════════════════════════════════════

class ProfileUpdateRequest(BaseModel):
    """Update the user's demographic profile (partial update — all fields optional)."""

    preferred_name: Optional[str] = Field(
        None, max_length=50, description="Preferred display name.",
    )
    age_range: Optional[str] = Field(
        None, description="Age range category.",
        example="31_50",
    )
    gender_identity: Optional[list[str]] = Field(
        None, description="Gender identity labels.",
        example=["non_binary"],
    )
    pronouns: Optional[str] = Field(
        None, max_length=50, description="Preferred pronouns.",
        example="they/them",
    )
    primary_language: Optional[str] = Field(
        None, description="Primary language.",
        example="English",
    )
    disability: Optional[list[str]] = Field(
        None, description="Disability types.",
        example=["cognitive", "visual"],
    )
    immigration_status: Optional[str] = Field(
        None, description="Immigration status.",
        example="citizen",
    )
    indigenous_identity: Optional[str] = Field(
        None, description="Indigenous identity.",
        example="non_indigenous",
    )
    education_level: Optional[str] = Field(
        None, description="Highest education level.",
        example="bachelors",
    )
    literacy_comfort_ai: Optional[int] = Field(
        None, ge=1, le=5, description="Comfort with AI (1=low, 5=high).",
    )
    profile_mode: Optional[str] = Field(
        None, description="Privacy mode: 'full' or 'general'.",
        example="full",
    )


class ProfileResponse(BaseModel):
    """Full demographic profile for the current user."""

    id: str = Field(..., description="Profile record ID.")
    user_id: str = Field(..., description="User ID this profile belongs to.")
    preferred_name: str = Field(..., description="Preferred display name.")
    age_range: Optional[str] = Field(None)
    gender_identity: list[str] = Field(default_factory=list)
    pronouns: Optional[str] = Field(None)
    primary_language: Optional[str] = Field(None)
    disability: list[str] = Field(default_factory=list)
    immigration_status: Optional[str] = Field(None)
    indigenous_identity: Optional[str] = Field(None)
    education_level: Optional[str] = Field(None)
    literacy_comfort_ai: Optional[int] = Field(None)
    profile_mode: str = Field("general")
    created_at: str = Field(..., description="ISO-8601 timestamp.")
    updated_at: str = Field(..., description="ISO-8601 timestamp.")


# ═══════════════════════════════════════════════════════════════════════════════
# Consent
# ═══════════════════════════════════════════════════════════════════════════════

class ConsentUpdateRequest(BaseModel):
    """Update privacy & research consent preferences."""

    profile_mode: Optional[str] = Field(
        None, description="Privacy mode: 'full' or 'general'.",
    )
    research_data_consent: Optional[bool] = Field(
        None, description="Allow anonymised data for research.",
    )


class ConsentResponse(BaseModel):
    """Current consent preferences for the user."""

    id: str = Field(..., description="Consent record ID.")
    user_id: str = Field(..., description="User ID.")
    profile_mode: str = Field("general")
    research_data_consent: bool = Field(False)
    has_consented: bool = Field(False, description="True if consent flow was completed.")
    consented_at: Optional[str] = Field(None)
    updated_at: Optional[str] = Field(None)
