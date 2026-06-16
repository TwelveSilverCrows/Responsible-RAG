from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import RedirectResponse

from app.auth.email import send_verification_email
from app.auth.email_auth import hash_password, verify_password
from app.auth.jwt import create_token, decode_token
from app.auth.oauth import exchange_code, get_google_auth_url, get_google_user
from app.config import settings
from app.db import users_collection
from app.models import TokenResponse, UserCreate, UserLogin

router = APIRouter(prefix="/auth", tags=["auth"])


# ── helpers ──────────────────────────────────────────────────────────────────

def _serialize(user: dict) -> dict:
    user = dict(user)
    user["id"] = str(user.pop("_id"))
    user.pop("hashed_password", None)
    return user


# ── email+password registration ──────────────────────────────────────────────

@router.post("/register", status_code=201)
async def register(body: UserCreate, bg: BackgroundTasks):
    if users_collection.find_one({"email": body.email}):
        raise HTTPException(400, "Email already registered")

    doc = {
        "email": body.email,
        "name": body.name,
        "provider": "email",
        "role": "user",
        "hashed_password": hash_password(body.password),
        "verified": False,
        "created_at": datetime.utcnow(),
        "google_id": None,
    }
    users_collection.insert_one(doc)

    token = create_token(
        {"sub": body.email, "purpose": "verify"},
        expires_delta=60 * 24,
    )
    bg.add_task(send_verification_email, body.email, token)

    return {"message": "Registered. Check your email to verify your account."}


# ── email verification (link in email) ───────────────────────────────────────

@router.get("/verify-email")
async def verify_email(token: str):
    payload = decode_token(token)
    if payload.get("purpose") != "verify":
        raise HTTPException(400, "Invalid token purpose")

    result = users_collection.update_one(
        {"email": payload["sub"]},
        {"$set": {"verified": True}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "User not found")

    return RedirectResponse(f"{settings.FRONTEND_URL}/login?verified=true")


# ── email+password login ──────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin):
    user = users_collection.find_one({"email": body.email, "provider": "email"})
    if not user:
        raise HTTPException(401, "Invalid credentials")
    if not user.get("verified"):
        raise HTTPException(401, "Email not verified. Check your inbox.")
    if not verify_password(body.password, user["hashed_password"]):
        raise HTTPException(401, "Invalid credentials")

    token = create_token({"sub": user["email"], "role": user["role"]})
    return {"access_token": token}


# ── Google OAuth ──────────────────────────────────────────────────────────────

@router.get("/google")
async def google_login():
    return RedirectResponse(get_google_auth_url())


@router.get("/google/callback")
async def google_callback(code: str):
    try:
        token_data = await exchange_code(code)
        guser = await get_google_user(token_data["access_token"])
    except Exception as exc:
        raise HTTPException(400, f"Google OAuth error: {exc}")

    email = guser["email"]
    existing = users_collection.find_one({"email": email})

    if not existing:
        users_collection.insert_one(
            {
                "email": email,
                "name": guser.get("name", ""),
                "provider": "google",
                "role": "user",
                "hashed_password": None,
                "verified": True,
                "created_at": datetime.utcnow(),
                "google_id": guser["id"],
            }
        )
        role = "user"
    else:
        role = existing.get("role", "user")

    jwt = create_token({"sub": email, "role": role})
    return RedirectResponse(f"{settings.FRONTEND_URL}/auth/callback?token={jwt}")


# ── admin login (.env credentials) ───────────────────────────────────────────

@router.post("/admin/login", response_model=TokenResponse)
async def admin_login(body: UserLogin):
    if body.email != settings.ADMIN_EMAIL or body.password != settings.ADMIN_PASSWORD:
        raise HTTPException(401, "Invalid admin credentials")

    token = create_token({"sub": "admin", "role": "admin"}, expires_delta=60 * 8)
    return {"access_token": token}
