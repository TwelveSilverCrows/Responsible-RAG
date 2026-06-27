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
    requiring attention.

    Admin-only.
    """
    from src.api.services.source_service import SourceService
    source_service = SourceService()
    stats = source_service.get_stats()
    return StatsResponse(**stats)
