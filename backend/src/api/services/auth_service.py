"""
services/auth_service.py — Authentication business logic
==========================================================
Dev-mode authentication using a single dummy admin user configured
via environment variables, plus Google OAuth ID token verification.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
import requests

from src.api.db.models import User
from src.core.config import get_settings


@dataclass
class AuthResult:
    """Result of a login or registration attempt."""

    user: User
    access_token: str
    refresh_token: str
    is_new_user: bool = False


def _now_ts() -> int:
    """Current UTC epoch seconds."""
    return int(datetime.now(timezone.utc).timestamp())


def create_access_token(user: User, auth_method: str = "password") -> str:
    """Issue a short-lived JWT access token."""
    settings = get_settings()
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "auth_method": auth_method,
        "iat": _now_ts(),
        "exp": _now_ts() + settings.auth_token_expire_minutes * 60,
    }
    return jwt.encode(payload, settings.auth_secret_key, algorithm=settings.auth_algorithm)


def create_refresh_token(user: User) -> str:
    """Issue a longer-lived JWT refresh token (7 days)."""
    settings = get_settings()
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "iat": _now_ts(),
        "exp": _now_ts() + 7 * 24 * 3600,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.auth_secret_key, algorithm=settings.auth_algorithm)


def decode_token(token: str) -> dict | None:
    """Decode and verify a JWT.  Returns the payload dict, or None if invalid."""
    settings = get_settings()
    try:
        return jwt.decode(token, settings.auth_secret_key, algorithms=[settings.auth_algorithm])
    except jwt.PyJWTError:
        return None


def verify_google_id_token(id_token: str) -> Optional[dict]:
    """
    Verify a Google ID token and return the user info payload.

    Uses ``google.oauth2.id_token.verify_oauth2_token`` which fetches
    Google's public certs and validates the token signature, audience,
    and expiration automatically.

    Also supports Google access tokens by calling Google's tokeninfo
    endpoint as a fallback.

    Returns ``None`` if verification fails.
    """
    # First try: verify as an ID token (JWT signed by Google)
    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests

        settings = get_settings()
        if not settings.google_client_id:
            return None

        info = google_id_token.verify_oauth2_token(
            id_token,
            google_requests.Request(),
            settings.google_client_id,
        )
        return info
    except Exception:
        pass

    # Second try: verify as an access token via Google's tokeninfo endpoint
    try:
        import requests
        resp = requests.get(
            "https://www.googleapis.com/oauth2/v3/tokeninfo",
            params={"access_token": id_token},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            # Map tokeninfo response to standard fields
            return {
                "sub": data.get("sub", ""),
                "email": data.get("email", ""),
                "name": data.get("name", ""),
                "email_verified": data.get("email_verified") == "true",
                "picture": data.get("picture", ""),
            }
    except Exception:
        pass

    return None


class AuthService:
    """
    Authentication service supporting both password-based and Google OAuth login.
    """

    @staticmethod
    async def login(email: str, password: str) -> AuthResult:
        """
        Authenticate with email + password against the dummy admin user.

        Raises ``ValueError`` if credentials don't match.
        """
        settings = get_settings()

        if email != settings.dummy_admin_email or password != settings.dummy_admin_password:
            raise ValueError("Invalid email or password")

        user = User(
            id="admin-dev",
            email=email,
            display_name="Admin",
            role="admin",
            email_verified=True,
        )

        return AuthResult(
            user=user,
            access_token=create_access_token(user),
            refresh_token=create_refresh_token(user),
            is_new_user=False,
        )

    @staticmethod
    async def google_auth(id_token: str) -> AuthResult:
        """
        Authenticate via Google ID token.

        Verifies the token with Google, then creates or returns an existing
        user.  In dev mode, this creates a lightweight in-memory user.

        Raises ``ValueError`` if the token is invalid.
        """
        info = verify_google_id_token(id_token)
        if info is None:
            raise ValueError("Invalid Google ID token")

        google_id = info.get("sub", "")
        email = info.get("email", "")
        name = info.get("name", email.split("@")[0] if email else "Google User")

        # In dev mode, create/find user from Google info
        # (In production, look up or create in MongoDB)
        user = User(
            id=f"google-{google_id}",
            email=email,
            display_name=name,
            role="client",
            email_verified=info.get("email_verified", False),
            google_id=google_id,
        )

        # TODO: store/retrieve user in MongoDB when available

        return AuthResult(
            user=user,
            access_token=create_access_token(user, auth_method="google"),
            refresh_token=create_refresh_token(user),
            is_new_user=True,
        )

    @staticmethod
    async def register(
        email: str,
        password: str,
        display_name: str,
    ) -> AuthResult:
        """Register is not available in dev mode."""
        raise NotImplementedError("Registration is not available in dev mode")

    @staticmethod
    async def verify_email(token: str) -> bool:
        """Email verification is not available in dev mode."""
        raise NotImplementedError("Email verification is not available in dev mode")
