from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.auth.email_auth import hash_password
from app.auth.jwt import get_admin_user
from app.db import users_collection
from app.models import AdminUserUpdate

router = APIRouter(prefix="/admin", tags=["admin"])


def _to_oid(user_id: str) -> ObjectId:
    try:
        return ObjectId(user_id)
    except Exception:
        raise HTTPException(400, "Invalid user ID format")


def _get_or_404(user_id: str) -> dict:
    user = users_collection.find_one({"_id": _to_oid(user_id)})
    if not user:
        raise HTTPException(404, "User not found")
    return user


def _serialize(user: dict) -> dict:
    user = dict(user)
    user["id"] = str(user.pop("_id"))
    user.pop("hashed_password", None)
    return user


@router.get("/users")
async def list_users(_: dict = Depends(get_admin_user)):
    return [_serialize(u) for u in users_collection.find()]


@router.get("/users/{user_id}")
async def get_user(user_id: str, _: dict = Depends(get_admin_user)):
    return _serialize(_get_or_404(user_id))


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    body: AdminUserUpdate,
    _: dict = Depends(get_admin_user),
):
    _get_or_404(user_id)  # 404 guard

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

    oid = _to_oid(user_id)
    users_collection.update_one({"_id": oid}, {"$set": fields})
    return _serialize(users_collection.find_one({"_id": oid}))


@router.delete("/users/{user_id}", status_code=200)
async def delete_user(user_id: str, _: dict = Depends(get_admin_user)):
    _get_or_404(user_id)
    users_collection.delete_one({"_id": _to_oid(user_id)})
    return {"message": "User deleted"}
