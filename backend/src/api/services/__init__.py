"""
services/__init__.py — Business logic layer
=============================================
Each service encapsulates a domain concern and operates on MongoDB
via ``Repository`` instances.  Services are **stateless** — they're
instantiated per-request or used as free functions.

Low-memory note:
    Services should NOT hold long-lived references to large objects
    (like the full RAG chain).  That belongs in ``api/deps.py``.
"""

from src.api.services.auth_service import AuthService
from src.api.services.user_service import UserService
from src.api.services.chat_service import ChatService
from src.api.services.source_service import SourceService
from src.api.services.feedback_service import FeedbackService

__all__ = [
    "AuthService",
    "UserService",
    "ChatService",
    "SourceService",
    "FeedbackService",
]
