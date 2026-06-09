"""
schemas/__init__.py — Re-export all Pydantic models
=====================================================
Import convenience::

    from src.api.schemas import ChatRequest, UserResponse, ...
"""

# Auth
from src.api.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    LoginResponse,
    GoogleAuthRequest,
    VerifyEmailRequest,
    ResetPasswordRequest,
    SetNewPasswordRequest,
    UserResponse,
    TokenResponse,
)

# Profile & Consent
from src.api.schemas.profile import (
    ProfileResponse,
    ProfileUpdateRequest,
    ConsentResponse,
    ConsentUpdateRequest,
    ProfileMode,
)

# Chat
from src.api.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatStreamRequest,
    ConversationResponse,
    ConversationListItem,
    ConversationListResponse,
    MessageResponse,
    CreateConversationRequest,
    RenameConversationRequest,
    CitationSchema,
)

# Source / Documents
from src.api.schemas.source import (
    SourceResponse,
    SourceListResponse,
    SourceCreateRequest,
    SourceUpdateRequest,
    UploadResponse as SourceUploadResponse,
    SourceType,
    SourceStatus,
)

# Feedback
from src.api.schemas.feedback import (
    FeedbackSubmitRequest,
    FeedbackResponse,
    MessageFeedbackRequest,
)

# Common
from src.api.schemas.common import (
    ErrorResponse,
    PaginationParams,
    PaginatedResponse,
    StatsResponse,
)

__all__ = [
    # Auth
    "RegisterRequest",
    "LoginRequest",
    "LoginResponse",
    "GoogleAuthRequest",
    "VerifyEmailRequest",
    "ResetPasswordRequest",
    "SetNewPasswordRequest",
    "UserResponse",
    "TokenResponse",
    # Profile
    "ProfileResponse",
    "ProfileUpdateRequest",
    "ConsentResponse",
    "ConsentUpdateRequest",
    "ProfileMode",
    # Chat
    "ChatRequest",
    "ChatResponse",
    "ChatStreamRequest",
    "ConversationResponse",
    "ConversationListItem",
    "ConversationListResponse",
    "MessageResponse",
    "CreateConversationRequest",
    "RenameConversationRequest",
    "CitationSchema",
    # Source
    "SourceResponse",
    "SourceListResponse",
    "SourceCreateRequest",
    "SourceUpdateRequest",
    "SourceUploadResponse",
    "SourceType",
    "SourceStatus",
    # Feedback
    "FeedbackSubmitRequest",
    "FeedbackResponse",
    "MessageFeedbackRequest",
    # Common
    "ErrorResponse",
    "PaginationParams",
    "PaginatedResponse",
    "StatsResponse",
]
