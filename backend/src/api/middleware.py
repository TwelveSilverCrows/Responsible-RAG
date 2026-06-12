"""
api/middleware.py — Auth & security middleware
================================================
JWT verification, role-based access control, and request-scoped user context.

Low-memory design:
    - JWT decoding is stateless (no DB lookup for every request).
    - User info is attached to ``request.state.user`` via a lightweight
      ``Depends`` callable, not a middleware class.

Usage:
    from src.api.middleware import get_current_user, require_admin
    from src.api.db.models import User

    @router.get("/admin/stats")
    async def dashboard(user: User = Depends(require_admin)):
        ...
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from src.api.db.models import User
from src.api.services.auth_service import decode_token

# FastAPI's built-in bearer token extractor
# (no cookie management, no session state — pure stateless JWT)
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[User]:
    """
    Extract and verify the JWT from the ``Authorization: Bearer <token>`` header.

    Returns ``None`` if no token is provided (anonymous access allowed).
    Raises 401 if the token is invalid or expired.
    """
    if credentials is None:
        return None

    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return User(
        id=payload.get("sub", "unknown"),
        email=payload.get("email", ""),
        display_name="Admin",
        role=payload.get("role", "admin"),
        email_verified=True,
    )


async def require_current_user(
    user: Optional[User] = Depends(get_current_user),
) -> User:
    """
    Like ``get_current_user`` but raises 401 if no user is authenticated.

    Use for endpoints that MUST have a logged-in user.
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def require_admin(
    user: User = Depends(require_current_user),
) -> User:
    """
    Require the current user to have the ``admin`` role.

    Use for admin-only endpoints (dashboard, source management, etc.).
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return user
