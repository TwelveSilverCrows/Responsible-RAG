"""
routes/admin/alerts.py — Admin system alerts
==============================================
Endpoints:
    GET  /api/v1/admin/alerts       — List system alerts (embedding quota, etc.)
    POST /api/v1/admin/alerts/resolve — Mark an alert as resolved

All endpoints are admin-only.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from src.api.middleware import require_admin
from src.api.schemas.admin_alert import AdminAlertResponse, AdminAlertListResponse

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_alerts_from_db() -> list[dict]:
    """Fetch alerts from MongoDB (returns empty list if unavailable)."""
    try:
        from src.api.db.database import get_database

        db = get_database()
        if db is not None:
            return list(
                db["admin_alerts"]
                .find()
                .sort("timestamp", -1)
                .limit(100)
            )
    except Exception as exc:
        logger.debug("Could not fetch admin alerts from MongoDB: %s", exc)
    return []


def _doc_to_alert(doc: dict) -> dict:
    """Convert a MongoDB document to a dict matching AdminAlertResponse."""
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id", ""))
    return doc


@router.get("", response_model=AdminAlertListResponse)
def list_alerts(
    admin: dict = Depends(require_admin),
):
    """Return all system alerts, sorted newest-first."""
    raw_alerts = _get_alerts_from_db()
    alerts = [_doc_to_alert(a) for a in raw_alerts]
    unresolved = sum(1 for a in alerts if a.get("resolved", "false") == "false")
    return AdminAlertListResponse(
        alerts=[AdminAlertResponse(**a) for a in alerts],
        total=len(alerts),
        unresolved_count=unresolved,
    )


@router.post("/resolve")
def resolve_alert(
    alert_id: str,
    admin: dict = Depends(require_admin),
):
    """Mark a specific alert as resolved."""
    try:
        from bson import ObjectId
        from src.api.db.database import get_database

        db = get_database()
        if db is not None:
            result = db["admin_alerts"].update_one(
                {"_id": ObjectId(alert_id)},
                {"$set": {"resolved": "true"}},
            )
            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Alert not found")
            return {"status": "resolved", "alert_id": alert_id}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to resolve alert %s: %s", alert_id, exc)
        raise HTTPException(status_code=500, detail="Failed to resolve alert")


