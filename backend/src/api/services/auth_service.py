"""
services/auth_service.py — Authentication business logic
==========================================================
Handles registration, login, password hashing, JWT issuance, email
verification tokens, and Google OAuth integration.

All methods are ``@staticmethod`` or free functions — no state to manage.

TODO (implement these):
    - ``hash_password(plain: str) -> str`` — bcrypt hashing.
    - ``verify_password(plain: str, hash: str) -> bool`` — bcrypt verify.
    - ``create_access_token(user: User) -> str`` — JWT encode.
    - ``create_refresh_token(user: User) -> str`` — longer-lived JWT.
    - ``decode_token(token: str) -> dict`` — JWT decode/verify.
    - ``generate_verification_token() -> str`` — crypto-safe random token.
"""

from dataclasses import dataclass
from typing import Optional
from src.api.db.models import User


@dataclass
class AuthResult:
    """Result of a login or registration attempt."""

    user: User
    access_token: str
    refresh_token: str
    is_new_user: bool = False


class AuthService:
    """
    Authentication service.

    Usage:
        result = AuthService.register(email="a@b.com", password="...", name="Alex")
        # or
        result = AuthService.login(email="a@b.com", password="...")
    """

    @staticmethod
    async def register(
        email: str,
        password: str,
        display_name: str,
    ) -> AuthResult:
        """
        Register a new user account.

        1. Check email uniqueness.
        2. Hash password.
        3. Insert User document.
        4. Generate verification token.
        5. Issue JWT pair.
        6. (Optionally) send verification email.

        Returns AuthResult with tokens + is_new_user=True.
        """
        # TODO: Implement
        # existing = await users_repo.find_one({"email": email})
        # if existing:
        #     raise HTTPException(409, "Email already registered")
        # hashed = hash_password(password)
        # user = User(email=email, password_hash=hashed, display_name=display_name)
        # user_id = await users_repo.insert_one(user)
        # token = create_access_token(user)
        # ...
        raise NotImplementedError("TODO: implement register")

    @staticmethod
    async def login(email: str, password: str) -> AuthResult:
        """
        Authenticate with email + password.

        1. Look up user by email.
        2. Verify password hash.
        3. Issue JWT pair.
        """
        # TODO: Implement
        raise NotImplementedError("TODO: implement login")

    @staticmethod
    async def google_auth(id_token: str) -> AuthResult:
        """
        Authenticate or register via Google OAuth.

        1. Verify the Google ID token.
        2. Extract email, name, google_id from payload.
        3. If user exists by google_id or email → login.
        4. Otherwise → create new user.
        """
        # TODO: Implement
        raise NotImplementedError("TODO: implement google_auth")

    @staticmethod
    async def verify_email(token: str) -> bool:
        """
        Verify a user's email address using a verification token.
        """
        # TODO: Implement
        raise NotImplementedError("TODO: implement verify_email")

    @staticmethod
    async def request_password_reset(email: str) -> bool:
        """
        Generate a reset token and (optionally) email it to the user.
        Always returns True to prevent email enumeration.
        """
        # TODO: Implement
        raise NotImplementedError("TODO: implement request_password_reset")

    @staticmethod
    async def set_new_password(token: str, new_password: str) -> bool:
        """
        Validate reset token and update the password.
        """
        # TODO: Implement
        raise NotImplementedError("TODO: implement set_new_password")
