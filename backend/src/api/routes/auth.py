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

from fastapi import APIRouter, Depends, HTTPException
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
from src.api.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register",
    response_model=LoginResponse,
    status_code=201,
    responses={409: {"model": ErrorResponse}},
)
async def register(body: RegisterRequest):
    """
    Register a new user account.

    Creates the user, generates a verification token, and returns
    JWT tokens.  The client should redirect to email verification
    if ``user.email_verified`` is false.
    """
    # TODO: Implement
    # result = await AuthService.register(
    #     email=body.email,
    #     password=body.password,
    #     display_name=body.display_name,
    # )
    # return LoginResponse(
    #     access_token=result.access_token,
    #     refresh_token=result.refresh_token,
    #     user=UserResponse.model_validate(result.user),
    #     is_new_user=result.is_new_user,
    # )
    raise NotImplementedError("TODO: implement register")


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={401: {"model": ErrorResponse}},
)
async def login(body: LoginRequest):
    """
    Authenticate with email and password.

    Returns JWT access + refresh tokens.
    """
    # TODO: Implement
    raise NotImplementedError("TODO: implement login")


@router.post(
    "/google",
    response_model=LoginResponse,
    responses={401: {"model": ErrorResponse}},
)
async def google_auth(body: GoogleAuthRequest):
    """
    Authenticate or register via Google OAuth.

    Send the Google ID token obtained from the frontend's OAuth flow.
    """
    # TODO: Implement
    raise NotImplementedError("TODO: implement google_auth")


@router.post(
    "/verify-email",
    response_model=dict,
)
async def verify_email(body: VerifyEmailRequest):
    """
    Verify email address using the token from the verification link.
    """
    # TODO: Implement
    raise NotImplementedError("TODO: implement verify_email")


@router.post(
    "/reset-password",
    response_model=dict,
)
async def reset_password(body: ResetPasswordRequest):
    """
    Request a password reset email.

    Always returns 200 to prevent email enumeration.
    """
    # TODO: Implement
    raise NotImplementedError("TODO: implement reset_password")


@router.post(
    "/reset-password/confirm",
    response_model=dict,
)
async def confirm_reset_password(body: SetNewPasswordRequest):
    """
    Set a new password using the token from the reset email.
    """
    # TODO: Implement
    raise NotImplementedError("TODO: implement confirm_reset_password")


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(refresh_token: str):
    """
    Issue a new access token using a valid refresh token.
    """
    # TODO: Implement
    raise NotImplementedError("TODO: implement refresh_token")


@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_me(user: User = Depends(require_current_user)):
    """
    Get the currently authenticated user's profile.

    Useful for session validation on page load.
    """
    # TODO: Return real user data
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        email_verified=user.email_verified,
        onboarding_completed=user.onboarding_completed,
        created_at=user.created_at,
    )
