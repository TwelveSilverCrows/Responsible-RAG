"""
services/feedback_service.py — Feedback handling
===================================================
Stores user feedback (per-message thumbs up/down and general feedback
forms) in MongoDB.

Low-memory design:
    - Feedback is write-heavy, read-light.  No caching needed.
    - Each feedback record is small and independent.
"""

from typing import Optional
from src.api.db.models import Feedback


class FeedbackService:
    """
    Feedback recording.

    Usage:
        service = FeedbackService()
        fb = await service.record_message_feedback(
            user_id=uid, conversation_id=cid, message_id=mid, rating="up"
        )
    """

    def __init__(self):
        # self.feedback = Repository[Feedback]("feedback", Feedback)
        pass

    async def record_message_feedback(
        self,
        user_id: Optional[str],
        conversation_id: str,
        message_id: str,
        rating: str,
        comment: Optional[str] = None,
    ) -> Feedback:
        """
        Record thumbs up/down feedback on a specific message.

        The ``user_id`` can be None if the user is anonymous.
        """
        # TODO: Implement
        # fb = Feedback(
        #     user_id=user_id,
        #     conversation_id=conversation_id,
        #     message_id=message_id,
        #     feedback_type=f"thumbs_{rating}",
        #     comment=comment,
        # )
        # await self.feedback.insert_one(fb)
        # return fb
        raise NotImplementedError("TODO: implement record_message_feedback")

    async def record_general_feedback(
        self,
        user_id: Optional[str],
        feedback_type: str,
        subject: Optional[str],
        message: str,
    ) -> Feedback:
        """
        Record general feedback from the feedback page.
        """
        # TODO: Implement
        raise NotImplementedError("TODO: implement record_general_feedback")
