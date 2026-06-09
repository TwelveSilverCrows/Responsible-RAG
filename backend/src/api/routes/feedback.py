"""
routes/feedback.py — Feedback endpoints
=========================================
Endpoints:
    POST /api/v1/feedback/message  — Rate a specific message (thumbs up/down)
    POST /api/v1/feedback          — Submit general feedback
"""

from fastapi import APIRouter, Depends
from src.api.schemas.feedback import (
    MessageFeedbackRequest,
    FeedbackSubmitRequest,
    FeedbackResponse,
)
from src.api.middleware import get_current_user
from src.api.db.models import User
from src.api.services.feedback_service import FeedbackService

router = APIRouter()


@router.post("/message", response_model=FeedbackResponse)
async def submit_message_feedback(
    body: MessageFeedbackRequest,
    user: User | None = Depends(get_current_user),
):
    """
    Record thumbs up / thumbs down feedback on a specific chat message.

    Works for both authenticated and anonymous users.
    """
    # TODO: Implement
    # service = FeedbackService()
    # fb = await service.record_message_feedback(
    #     user_id=user.id if user else None,
    #     conversation_id=body.conversation_id,
    #     message_id=body.message_id,
    #     rating=body.rating,
    #     comment=body.comment,
    # )
    # return FeedbackResponse(id=fb.id, status="recorded")
    raise NotImplementedError("TODO: implement submit_message_feedback")


@router.post("", response_model=FeedbackResponse)
async def submit_general_feedback(
    body: FeedbackSubmitRequest,
    user: User | None = Depends(get_current_user),
):
    """
    Submit general feedback from the feedback page.

    Not tied to any specific conversation or message.
    """
    # TODO: Implement
    raise NotImplementedError("TODO: implement submit_general_feedback")
