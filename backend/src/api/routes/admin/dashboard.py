"""
routes/admin/dashboard.py — Admin dashboard endpoints
========================================================
Endpoints:
    GET /api/v1/admin/dashboard/stats  — Aggregate platform statistics
"""

from fastapi import APIRouter, Depends
from src.api.schemas.common import StatsResponse
from src.api.middleware import require_admin
from src.api.db.models import User

router = APIRouter()


@router.get("/stats", response_model=StatsResponse)
async def get_dashboard_stats(admin: User = Depends(require_admin)):
    """
    Get aggregate statistics for the admin dashboard.

    Returns counts of sources, conversations, users, and items
    requiring attention (processing, errors, incomplete metadata).

    Admin-only.
    """
    # TODO: Implement
    # from src.api.services.source_service import SourceService
    # source_service = SourceService()
    # stats = await source_service.get_stats()
    # return StatsResponse(**stats)
    return StatsResponse(
        total_sources=0,
        indexed_sources=0,
        processing_sources=0,
        error_sources=0,
        total_conversations=0,
        total_users=0,
        incomplete_metadata=0,
    )
