"""
schemas/auth.py — Authentication & user management
=====================================================
Covers: register, login, Google OAuth, email verification, password reset.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════════════
# Requests
# ═══════════════════════════════════════════════════════════════════════════════

class RegisterRequest(BaseModel):
    """Register a new user account."""

    email: EmailStr = Field(
        ..., description="User's email address.",
        example="user@example.ca",
    )
    password: str = Field(
        ..., min_length=8, max_length=128,
        description="Password (min 8 characters).",
    )
    display_name: str = Field(
        ..., min_length=1, max_length=50,
        description="Public display name.",
        example="Alex M.",
    )


class LoginRequest(BaseModel):
    """Authenticate with email/username + password."""

    email: str = Field(
        ..., description="Registered email or username.",
        example="admin",
    )
    password: str = Field(
        ..., min_length=1,
        description="Account password.",
    )


class GoogleAuthRequest(BaseModel):
    """Authenticate or register via Google OAuth."""

    id_token: str = Field(
        ..., description="Google ID token from the OAuth flow.",
    )


class VerifyEmailRequest(BaseModel):
    """Verify email address using a token sent to the user."""

    token: str = Field(
        ..., description="Verification token from email link.",
    )


class ResetPasswordRequest(BaseModel):
    """Request a password-reset email."""

    email: EmailStr = Field(
        ..., description="Email of the account to reset.",
    )


class SetNewPasswordRequest(BaseModel):
    """Set a new password using a reset token."""

    token: str = Field(
        ..., description="Reset token from email link.",
    )
    password: str = Field(
        ..., min_length=8, max_length=128,
        description="New password.",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Responses
# ═══════════════════════════════════════════════════════════════════════════════

class UserResponse(BaseModel):
    """Public-facing user info (no password hash or tokens)."""

    id: str = Field(..., description="User ID.")
    email: str = Field(..., description="Email address.")
    display_name: str = Field(..., description="Display name.")
    role: str = Field(..., description="'client' or 'admin'.")
    email_verified: bool = Field(..., description="Whether email is verified.")
    onboarding_completed: bool = Field(
        ..., description="Whether onboarding flow is done.",
    )
    created_at: str = Field(..., description="ISO-8601 registration timestamp.")


class TokenResponse(BaseModel):
    """JWT token pair returned after authentication."""

    access_token: str = Field(
        ..., description="JWT access token (short-lived, ~15 min).",
    )
    refresh_token: str = Field(
        ..., description="JWT refresh token (long-lived, ~7 days).",
    )
    token_type: str = Field("bearer", description="Token type.")

    # User info bundled with the token to avoid a second API call
    user: UserResponse = Field(..., description="Authenticated user object.")


class LoginResponse(BaseModel):
    """Response body for successful login / registration."""

    access_token: str = Field(..., description="JWT access token.")
    refresh_token: str = Field(..., description="JWT refresh token.")
    token_type: str = Field("bearer")
    user: UserResponse = Field(..., description="Authenticated user.")
    is_new_user: bool = Field(
        False, description="True if this was a first-time registration.",
    )
