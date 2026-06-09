"""
db/__init__.py — MongoDB data access layer
============================================

Minimal, framework-agnostic MongoDB helpers. Designed for low memory:

- No ODM overhead (no MongoEngine, Beanie, etc.).
- ``mongomock`` for local dev (optional, not imported here).
- ``pymongo`` for production with connection pooling.
- All collections are accessed via the ``Repository`` generic class.
"""

from src.api.db.repository import Repository
from src.api.db.models import (
    User,
    UserProfile,
    ConsentRecord,
    Conversation,
    Message,
    Source,
    SourceChunk,
    Feedback,
)

__all__ = [
    "Repository",
    "User",
    "UserProfile",
    "ConsentRecord",
    "Conversation",
    "Message",
    "Source",
    "SourceChunk",
    "Feedback",
]
