"""
routes/admin/dashboard.py — Admin dashboard endpoints
========================================================
Endpoints:
    GET /api/v1/admin/dashboard/stats  — Aggregate platform statistics
"""

from fastapi import APIRouter, Depends
from src.api.schemas.common import StatsResponse
from src.api.middleware import require_admin

router = APIRouter()


@router.get("/stats", response_model=StatsResponse)
def get_dashboard_stats(admin: dict = Depends(require_admin)):
    """
    Get aggregate statistics for the admin dashboard.

    Returns counts of sources, conversations, users, and items
    requiring attention, plus embedding cooldown status.

    Admin-only.
    """
    from src.api.services.source_service import SourceService
    from src.core.embedding_quota import get_quota_monitor

    source_service = SourceService()
    stats = source_service.get_stats()

    # Embedding cooldown status
    monitor = get_quota_monitor()
    stats["embedding_cooldown_active"] = monitor.is_in_cooldown()
    stats["embedding_cooldown_remaining_seconds"] = monitor.get_cooldown_remaining()

    # Unresolved admin alerts count
    try:
        from src.api.db.database import get_database
        db = get_database()
        if db is not None:
            stats["unresolved_alerts"] = db["admin_alerts"].count_documents(
                {"resolved": "false"}
            )
        else:
            stats["unresolved_alerts"] = 0
    except Exception:
        stats["unresolved_alerts"] = 0

    return StatsResponse(**stats)
