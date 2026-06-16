"""Admin user management — matches fastapi_auth's admin.py."""

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from src.api.middleware import get_admin_user
from src.api.db.database import get_users_collection
from src.api.services.auth_service import hash_password, serialize_user
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class AdminUserUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    verified: Optional[bool] = None


def _to_oid(user_id: str) -> ObjectId:
    try:
        return ObjectId(user_id)
    except Exception:
        raise HTTPException(400, "Invalid user ID format")


def _get_or_404(user_id: str) -> dict:
    users = get_users_collection()
    user = users.find_one({"_id": _to_oid(user_id)})
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.get("")
async def list_users(_: dict = Depends(get_admin_user)):
    users = get_users_collection()
    return [serialize_user(u) for u in users.find()]


@router.get("/{user_id}")
async def get_user(user_id: str, _: dict = Depends(get_admin_user)):
    return serialize_user(_get_or_404(user_id))


@router.patch("/{user_id}")
async def update_user(
    user_id: str,
    body: AdminUserUpdate,
    _: dict = Depends(get_admin_user),
):
    _get_or_404(user_id)
    fields: dict = {}
    if body.name is not None:
        fields["name"] = body.name
    if body.password is not None:
        fields["hashed_password"] = hash_password(body.password)
    if body.role is not None:
        if body.role not in ("user", "admin"):
            raise HTTPException(400, "role must be 'user' or 'admin'")
        fields["role"] = body.role
    if body.verified is not None:
        fields["verified"] = body.verified
    if not fields:
        raise HTTPException(400, "Nothing to update")

    users = get_users_collection()
    oid = _to_oid(user_id)
    users.update_one({"_id": oid}, {"$set": fields})
    return serialize_user(users.find_one({"_id": oid}))


@router.delete("/{user_id}", status_code=200)
async def delete_user(user_id: str, _: dict = Depends(get_admin_user)):
    _get_or_404(user_id)
    users = get_users_collection()
    users.delete_one({"_id": _to_oid(user_id)})
    return {"message": "User deleted"}
