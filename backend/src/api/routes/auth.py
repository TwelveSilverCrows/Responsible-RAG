"""
routes/auth.py — Authentication endpoints
============================================
Endpoints:
    POST   /api/v1/auth/register          — Create account
    POST   /api/v1/auth/login             — Email + password login
    POST   /api/v1/auth/google            — Google OAuth
    POST   /api/v1/auth/verify-email      — Verify email address
    POST   /api/v1/auth/reset-password    — Request password reset
    POST   /api/v1/auth/reset-password/confirm  — Set new password
    POST   /api/v1/auth/refresh           — Refresh JWT token
    GET    /api/v1/auth/me                — Get current user info
"""

from fastapi import APIRouter, Depends, HTTPException, status
from src.api.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    GoogleAuthRequest,
    VerifyEmailRequest,
    ResetPasswordRequest,
    SetNewPasswordRequest,
    LoginResponse,
    UserResponse,
)
from src.api.schemas.common import ErrorResponse
from src.api.middleware import get_current_user, require_current_user
from src.api.db.models import User
from src.api.services.auth_service import AuthService, decode_token, create_access_token, create_refresh_token

router = APIRouter()


def _user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        email_verified=user.email_verified,
        onboarding_completed=True,
        created_at="",
    )


@router.post(
    "/register",
    status_code=501,
)
async def register(body: RegisterRequest):
    """Registration is not available in dev mode."""
    raise HTTPException(status_code=501, detail="Registration is not available in dev mode")


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={401: {"model": ErrorResponse}},
)
async def login(body: LoginRequest):
    """
    Authenticate with email and password against the dummy admin user.

    Returns JWT access + refresh tokens.
    """
    try:
        result = await AuthService.login(email=body.email, password=body.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )

    return LoginResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        token_type="bearer",
        user=_user_to_response(result.user),
        is_new_user=result.is_new_user,
    )


@router.post(
    "/google",
    response_model=LoginResponse,
    responses={401: {"model": ErrorResponse}},
)
async def google_auth(body: GoogleAuthRequest):
    """
    Authenticate with a Google ID token (client-side OAuth flow).

    Verifies the token with Google, creates/returns a user, and issues
    JWT access + refresh tokens.
    """
    try:
        result = await AuthService.google_auth(id_token=body.id_token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )

    return LoginResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        token_type="bearer",
        user=_user_to_response(result.user),
        is_new_user=result.is_new_user,
    )


@router.post("/verify-email", status_code=501)
async def verify_email(body: VerifyEmailRequest):
    raise HTTPException(status_code=501, detail="Not available in dev mode")


@router.post("/reset-password", status_code=501)
async def reset_password(body: ResetPasswordRequest):
    raise HTTPException(status_code=501, detail="Not available in dev mode")


@router.post("/reset-password/confirm", status_code=501)
async def confirm_reset_password(body: SetNewPasswordRequest):
    raise HTTPException(status_code=501, detail="Not available in dev mode")


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(token_body: dict):
    """
    Issue a new access token using a valid refresh token.
    """
    refresh = token_body.get("refresh_token", "")
    payload = decode_token(refresh)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = User(
        id=payload["sub"],
        email=payload.get("email", ""),
        display_name="Admin",
        role=payload.get("role", "admin"),
        email_verified=True,
    )
    return LoginResponse(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
        token_type="bearer",
        user=_user_to_response(user),
        is_new_user=False,
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_me(user: User = Depends(require_current_user)):
    """
    Get the currently authenticated user's profile.

    Useful for session validation on page load.
    """
    return _user_to_response(user)
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        email_verified=user.email_verified,
        onboarding_completed=user.onboarding_completed,
        created_at=user.created_at,
    )
