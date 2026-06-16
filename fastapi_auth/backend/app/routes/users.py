from fastapi import APIRouter, Depends, HTTPException
from app.auth.email_auth import hash_password
from app.auth.jwt import get_current_user
from app.db import users_collection
from app.models import UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


def _get_or_404(email: str) -> dict:
    user = users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(404, "User not found")
    return user


def _serialize(user: dict) -> dict:
    user = dict(user)
    user["id"] = str(user.pop("_id"))
    user.pop("hashed_password", None)
    return user


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") == "admin":
        raise HTTPException(403, "Admin has no profile here. Use /admin routes.")
    return _serialize(_get_or_404(current_user["sub"]))


@router.patch("/me")
async def update_me(body: UserUpdate, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") == "admin":
        raise HTTPException(403, "Admin has no profile here.")

    fields: dict = {}
    if body.name:
        fields["name"] = body.name
    if body.password:
        fields["hashed_password"] = hash_password(body.password)
    if not fields:
        raise HTTPException(400, "Nothing to update")

    users_collection.update_one({"email": current_user["sub"]}, {"$set": fields})
    return _serialize(_get_or_404(current_user["sub"]))


@router.delete("/me", status_code=200)
async def delete_me(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") == "admin":
        raise HTTPException(403, "Admin cannot delete self here.")

    result = users_collection.delete_one({"email": current_user["sub"]})
    if result.deleted_count == 0:
        raise HTTPException(404, "User not found")
    return {"message": "Account deleted"}
