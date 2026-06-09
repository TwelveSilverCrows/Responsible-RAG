"""
db/models.py — MongoDB document models as dataclasses
=======================================================
Plain ``@dataclass`` objects that mirror MongoDB document shapes.  No ORM
coupling — just data containers.

Why dataclasses (not Pydantic)?
    - Zero validation overhead at the DB layer (validation happens in schemas).
    - Lower memory footprint per object.
    - Easier to (de)serialise to/from dict for MongoDB driver.

Every model includes:
    - ``id`` (str) — the ``_id`` field in MongoDB.
    - ``to_dict()`` — serialise to a dict (omit None values optionally).
    - ``from_dict()`` — classmethod to hydrate from a MongoDB document.

Convention:
    - Timestamps are ISO-8601 strings (not datetime objects) to avoid
      serialisation issues across the wire.
    - Use ``field(default_factory=...)`` for mutable defaults.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _now_iso() -> str:
    """Return current UTC time as ISO-8601 string."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    """Return a new UUID4 string."""
    from uuid import uuid4
    return str(uuid4())


def _clean_dict(d: dict, skip_none: bool = True) -> dict:
    """Remove None values and convert ``_id`` field."""
    if skip_none:
        d = {k: v for k, v in d.items() if v is not None}
    if "_id" in d and "id" not in d:
        d["id"] = str(d.pop("_id"))
    return d


# ═══════════════════════════════════════════════════════════════════════════════
# User / Auth
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class User:
    """
    Registered user account.

    MongoDB collection: ``users``
    """
    id: str = field(default_factory=_new_id)
    email: str = ""
    password_hash: str = ""          # bcrypt hash
    display_name: str = ""
    role: str = "client"             # "client" | "admin"
    email_verified: bool = False
    verification_token: Optional[str] = None
    reset_token: Optional[str] = None
    reset_token_expires: Optional[str] = None
    google_id: Optional[str] = None  # for Google OAuth
    onboarding_completed: bool = False
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self, skip_none: bool = True) -> dict:
        d = asdict(self)
        d["_id"] = d.pop("id")
        return _clean_dict(d, skip_none)

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        data = _clean_dict(data)
        return cls(**data)


# ═══════════════════════════════════════════════════════════════════════════════
# User Profile (demographics)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class UserProfile:
    """
    Optional detailed demographics collected during onboarding.

    MongoDB collection: ``profiles``
    One-to-one with User (userId matches User.id).
    """
    id: str = field(default_factory=_new_id)
    user_id: str = ""
    preferred_name: str = ""
    age_range: Optional[str] = None          # "under_18" | "18_30" | ...
    gender_identity: list[str] = field(default_factory=list)
    pronouns: Optional[str] = None
    primary_language: Optional[str] = None
    disability: list[str] = field(default_factory=list)
    immigration_status: Optional[str] = None
    indigenous_identity: Optional[str] = None
    education_level: Optional[str] = None
    literacy_comfort_ai: Optional[int] = None  # 1–5
    profile_mode: str = "general"             # "full" | "general"
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self, skip_none: bool = True) -> dict:
        d = asdict(self)
        d["_id"] = d.pop("id")
        return _clean_dict(d, skip_none)

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        data = _clean_dict(data)
        return cls(**data)


# ═══════════════════════════════════════════════════════════════════════════════
# Consent
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ConsentRecord:
    """
    User's privacy & research consent choices.

    MongoDB collection: ``consent``
    One-to-one with User (userId matches User.id).
    """
    id: str = field(default_factory=_new_id)
    user_id: str = ""
    profile_mode: str = "general"        # "full" | "general"
    research_data_consent: bool = False  # anonymised data for research
    consented_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self, skip_none: bool = True) -> dict:
        d = asdict(self)
        d["_id"] = d.pop("id")
        return _clean_dict(d, skip_none)

    @classmethod
    def from_dict(cls, data: dict) -> "ConsentRecord":
        data = _clean_dict(data)
        return cls(**data)


# ═══════════════════════════════════════════════════════════════════════════════
# Chat
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Conversation:
    """
    A single chat conversation between a user and the RAG bot.

    MongoDB collection: ``conversations``
    """
    id: str = field(default_factory=_new_id)
    user_id: str = ""
    title: str = "New conversation"
    profile_key: Optional[str] = None     # audience profile used
    message_count: int = 0
    last_message: Optional[str] = None
    last_message_at: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self, skip_none: bool = True) -> dict:
        d = asdict(self)
        d["_id"] = d.pop("id")
        return _clean_dict(d, skip_none)

    @classmethod
    def from_dict(cls, data: dict) -> "Conversation":
        data = _clean_dict(data)
        return cls(**data)


@dataclass
class Message:
    """
    A single message within a conversation.

    MongoDB collection: ``messages``
    """
    id: str = field(default_factory=_new_id)
    conversation_id: str = ""
    role: str = "user"                    # "user" | "assistant"
    content: str = ""
    citations: list[dict] = field(default_factory=list)
    # Each citation: {"source_id": "...", "excerpt": "...", "number": 1}
    is_streaming: bool = False
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self, skip_none: bool = True) -> dict:
        d = asdict(self)
        d["_id"] = d.pop("id")
        return _clean_dict(d, skip_none)

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        data = _clean_dict(data)
        return cls(**data)


# ═══════════════════════════════════════════════════════════════════════════════
# Sources / Knowledge Base
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Source:
    """
    A document in the knowledge base (ingested into the vector store).

    MongoDB collection: ``sources``
    """
    id: str = field(default_factory=_new_id)
    title: str = ""
    source_type: str = "pdf"                # "pdf" | "text" | "audio" | "webpage" | "youtube"
    authors: list[str] = field(default_factory=list)
    publication_date: Optional[str] = None
    publisher: Optional[str] = None
    url: Optional[str] = None
    doi: Optional[str] = None
    language: Optional[str] = None
    description: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    content_sensitivity: str = "low"        # "low" | "medium" | "high"
    internal_notes: Optional[str] = None
    status: str = "queued"                  # "queued" | "processing" | "indexed" | "error"
    error_message: Optional[str] = None
    file_path: Optional[str] = None
    thumbnail_url: Optional[str] = None
    chunk_count: int = 0
    indexed_at: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self, skip_none: bool = True) -> dict:
        d = asdict(self)
        d["_id"] = d.pop("id")
        return _clean_dict(d, skip_none)

    @classmethod
    def from_dict(cls, data: dict) -> "Source":
        data = _clean_dict(data)
        return cls(**data)


@dataclass
class SourceChunk:
    """
    A single chunk of a source document stored in Chroma + referenced from Mongo.

    MongoDB collection: ``chunks`` (metadata only; vectors live in Chroma).
    """
    id: str = field(default_factory=_new_id)
    source_id: str = ""
    chunk_index: int = 0
    content: str = ""
    chroma_id: Optional[str] = None          # ID in Chroma vector store
    embedding_model: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self, skip_none: bool = True) -> dict:
        d = asdict(self)
        d["_id"] = d.pop("id")
        return _clean_dict(d, skip_none)

    @classmethod
    def from_dict(cls, data: dict) -> "SourceChunk":
        data = _clean_dict(data)
        return cls(**data)


# ═══════════════════════════════════════════════════════════════════════════════
# Feedback
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Feedback:
    """
    User feedback on a conversation or individual message.

    MongoDB collection: ``feedback``
    """
    id: str = field(default_factory=_new_id)
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    feedback_type: str = ""                  # "thumbs_up" | "thumbs_down" | "general"
    comment: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self, skip_none: bool = True) -> dict:
        d = asdict(self)
        d["_id"] = d.pop("id")
        return _clean_dict(d, skip_none)

    @classmethod
    def from_dict(cls, data: dict) -> "Feedback":
        data = _clean_dict(data)
        return cls(**data)
