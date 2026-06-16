"""Auth routes — matches fastapi_auth pattern."""

from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import RedirectResponse

from src.api.services.auth_service import (
    hash_password, verify_password,
    create_token, decode_token, create_verification_token,
    get_google_auth_url, exchange_google_code, get_google_user,
    get_backend_url, send_verification_email, serialize_user,
)
from src.api.middleware import get_current_user, get_admin_user
from src.api.db.database import get_users_collection
from src.core.config import get_settings
from pydantic import BaseModel, EmailStr
from typing import Optional

router = APIRouter()

# ── Schemas (inline, like fastapi_auth) ───────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ── Register ──────────────────────────────────────────────────────────────────

@router.post("/register", status_code=201)
async def register(body: UserCreate, bg: BackgroundTasks):
    users = get_users_collection()
    if users is None:
        raise HTTPException(503, "Database not available")
    if users.find_one({"email": body.email}):
        raise HTTPException(400, "Email already registered")

    doc = {
        "email": body.email,
        "name": body.name,
        "provider": "email",
        "role": "user",
        "hashed_password": hash_password(body.password),
        "verified": False,
        "onboarding_completed": False,
        "created_at": datetime.utcnow().isoformat(),
        "google_id": None,
    }
    users.insert_one(doc)

    token = create_verification_token(body.email)
    bg.add_task(send_verification_email, body.email, token)

    # In dev mode (SMTP not configured), return the verification URL
    settings = get_settings()
    resp = {"message": "Registered. Check your email to verify your account."}
    if not settings.smtp_user or not settings.smtp_password:
        verify_url = f"{get_backend_url()}/auth/verify-email?token={token}"
        resp["dev_verify_url"] = verify_url
    return resp

# ── Verify email ──────────────────────────────────────────────────────────────

@router.get("/verify-email")
async def verify_email(token: str):
    payload = decode_token(token)
    if payload is None or payload.get("purpose") != "verify":
        raise HTTPException(400, "Invalid token")

    users = get_users_collection()
    result = users.update_one(
        {"email": payload["sub"]},
        {"$set": {"verified": True}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "User not found")

    settings = get_settings()
    return RedirectResponse(f"{settings.frontend_url}/login?verified=true")

# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin):
    settings = get_settings()

    # Admin check first
    if body.email == settings.admin_email and body.password == settings.admin_password:
        token = create_token({"sub": "admin", "role": "admin"}, expires_delta=60 * 8)
        return {"access_token": token, "token_type": "bearer"}

    users = get_users_collection()
    if users is None:
        raise HTTPException(503, "Database not available")
    user = users.find_one({"email": body.email, "provider": "email"})
    if not user:
        raise HTTPException(401, "Invalid credentials")
    if not user.get("verified"):
        raise HTTPException(401, "Email not verified. Check your inbox.")
    if not verify_password(body.password, user["hashed_password"]):
        raise HTTPException(401, "Invalid credentials")

    needs_onboarding = not user.get("onboarding_completed", False)
    token = create_token({"sub": user["email"], "role": user["role"], "onboarding": needs_onboarding})
    return {"access_token": token, "token_type": "bearer"}

# ── Forgot / Reset password ───────────────────────────────────────────────────

@router.post("/forgot-password")
async def forgot_password(body: UserLogin):
    """Send a password reset email with a reset token."""
    users = get_users_collection()
    if users is None:
        raise HTTPException(503, "Database not available")

    user = users.find_one({"email": body.email, "provider": "email"})
    # Always return success to avoid email enumeration
    if not user:
        return {"message": "If an account exists, a reset link has been sent."}

    reset_token = create_token({"sub": body.email, "purpose": "reset"}, expires_delta=60)
    users.update_one({"email": body.email}, {"$set": {"reset_token": reset_token}})

    from src.api.services.auth_service import send_reset_email
    send_reset_email(body.email, reset_token)

    resp = {"message": "If an account exists, a reset link has been sent."}
    s = get_settings()
    if not s.smtp_user or not s.smtp_password:
        resp["dev_reset_url"] = f"{s.frontend_url}/auth/reset-password?token={reset_token}"
    return resp


@router.post("/reset-password")
async def reset_password(token: str, password: str):
    """Set a new password using a valid reset token."""
    payload = decode_token(token)
    if payload is None or payload.get("purpose") != "reset":
        raise HTTPException(400, "Invalid or expired reset token")

    users = get_users_collection()
    if users is None:
        raise HTTPException(503, "Database not available")

    user = users.find_one({"email": payload["sub"], "reset_token": token})
    if not user:
        raise HTTPException(400, "Invalid or expired reset token")

    users.update_one(
        {"email": payload["sub"]},
        {"$set": {"hashed_password": hash_password(password), "reset_token": None}},
    )
    return {"message": "Password reset successful. You can now sign in."}


# ── Google OAuth ──────────────────────────────────────────────────────────────

@router.get("/google")
async def google_login():
    return RedirectResponse(get_google_auth_url())

@router.get("/google/callback")
async def google_callback(code: str):
    try:
        token_data = await exchange_google_code(code)
        guser = await get_google_user(token_data["access_token"])
    except Exception as exc:
        raise HTTPException(400, f"Google OAuth error: {exc}")

    email = guser["email"]
    users = get_users_collection()
    existing = users.find_one({"email": email})

    is_new = False
    if not existing:
        users.insert_one({
            "email": email,
            "name": guser.get("name", ""),
            "provider": "google",
            "role": "user",
            "hashed_password": None,
            "verified": True,
            "onboarding_completed": False,
            "created_at": datetime.utcnow().isoformat(),
            "google_id": guser["id"],
        })
        role = "user"
        is_new = True
    else:
        role = existing.get("role", "user")
        # Existing user might still need onboarding
        needs_onboarding = not existing.get("onboarding_completed", False)
        if needs_onboarding:
            is_new = True

    jwt = create_token({"sub": email, "role": role, "onboarding": is_new})
    settings = get_settings()
    return RedirectResponse(f"{settings.frontend_url}/auth/callback?token={jwt}&is_new={str(is_new).lower()}")

# ── Admin login ───────────────────────────────────────────────────────────────

@router.post("/admin/login", response_model=TokenResponse)
async def admin_login(body: UserLogin):
    settings = get_settings()
    if body.email != settings.admin_email or body.password != settings.admin_password:
        raise HTTPException(401, "Invalid admin credentials")
    token = create_token({"sub": "admin", "role": "admin"}, expires_delta=60 * 8)
    return {"access_token": token, "token_type": "bearer"}

# ── Complete onboarding ───────────────────────────────────────────────────────

@router.post("/onboarding/complete")
async def complete_onboarding(current_user: dict = Depends(get_current_user)):
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

# ── Get /me ───────────────────────────────────────────────────────────────────

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") == "admin":
        return {"id": "admin", "email": current_user["sub"], "name": "Admin", "role": "admin", "verified": True}
    users = get_users_collection()
    user = users.find_one({"email": current_user["sub"]})
    if not user:
        raise HTTPException(404, "User not found")
    return serialize_user(user)
