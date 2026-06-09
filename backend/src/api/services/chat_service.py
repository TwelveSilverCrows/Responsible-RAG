"""
services/chat_service.py — Conversation & message management
==============================================================
Manages CRUD for conversations and messages, plus the core RAG invocation
(delegated to ``RAGChain`` from ``src.core``).

Low-memory design:
    - Conversations and messages are paginated — never load all history.
    - Streaming responses via async generator (no buffering).
    - The RAG chain is injected (not created here), keeping this service
      focused on data orchestration.
"""

from typing import Optional
from src.api.db.models import Conversation, Message


class ChatService:
    """
    Chat and conversation operations for a given user.

    Usage:
        service = ChatService(user_id="...")
        convos = await service.list_conversations()
        msg = await service.add_message(conv_id, role="user", content="...")
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        # self.conversations = Repository[Conversation]("conversations", Conversation)
        # self.messages = Repository[Message]("messages", Message)

    # ── Conversations ─────────────────────────────────────────────────────────

    async def list_conversations(
        self, page: int = 1, limit: int = 20,
    ) -> tuple[list[Conversation], int]:
        """
        List the user's conversations, most recent first.

        Returns (conversations, total_count).
        """
        # TODO: Implement
        # convos = await self.conversations.find_many(
        #     {"user_id": self.user_id},
        #     sort=[("updated_at", -1)],
        #     skip=(page - 1) * limit,
        #     limit=limit,
        # )
        # total = await self.conversations.count({"user_id": self.user_id})
        # return convos, total
        raise NotImplementedError("TODO: implement list_conversations")

    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID (scoped to the current user)."""
        # TODO: Implement
        raise NotImplementedError("TODO: implement get_conversation")

    async def create_conversation(
        self, title: Optional[str] = None, profile_key: Optional[str] = None,
    ) -> Conversation:
        """Create a new conversation."""
        # TODO: Implement
        raise NotImplementedError("TODO: implement create_conversation")

    async def rename_conversation(
        self, conversation_id: str, title: str,
    ) -> Optional[Conversation]:
        """Rename an existing conversation."""
        # TODO: Implement
        raise NotImplementedError("TODO: implement rename_conversation")

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages."""
        # TODO: Implement
        raise NotImplementedError("TODO: implement delete_conversation")

    # ── Messages ──────────────────────────────────────────────────────────────

    async def get_messages(
        self, conversation_id: str, page: int = 1, limit: int = 50,
    ) -> tuple[list[Message], int]:
        """Get paginated messages for a conversation (oldest first)."""
        # TODO: Implement
        raise NotImplementedError("TODO: implement get_messages")

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        citations: Optional[list[dict]] = None,
    ) -> Message:
        """
        Append a message to a conversation.

        If ``role == "assistant"``, also updates the conversation's
        ``last_message`` and bumps ``message_count``.
        """
        # TODO: Implement
        raise NotImplementedError("TODO: implement add_message")

    # ── RAG (delegates to src.core) ───────────────────────────────────────────

    async def ask_rag(
        self,
        question: str,
        conversation_id: str,
        profile_key: Optional[str] = None,
    ) -> dict:
        """
        Invoke the RAG pipeline, store both user message and assistant
        response, and return the result.

        Returns:
            {"answer": "...", "citations": [...], "message_id": "...", "conversation_id": "..."}
        """
        # TODO: Implement
        # from src.api.deps import get_rag_chain
        # chain = await get_rag_chain()
        # result = chain.invoke(question, profile_key)
        # msg = await self.add_message(conversation_id, "assistant", result.answer, result.citations)
        # return {"answer": result.answer, "citations": result.citations, ...}
        raise NotImplementedError("TODO: implement ask_rag")

    async def ask_rag_stream(
        self,
        question: str,
        conversation_id: str,
        profile_key: Optional[str] = None,
    ):
        """
        Async generator that yields streaming tokens from the RAG pipeline.

        Yields:
            dict — {"type": "token", "text": "..."} for each chunk.
            dict — {"type": "done", "citations": [...], "message_id": "..."} at the end.
        """
        # TODO: Implement streaming generator
        # chain = await get_rag_chain()
        # async for chunk in chain.astream(question, profile_key):
        #     yield {"type": "token", "text": chunk}
        # yield {"type": "done", "citations": [...], "message_id": "..."}
        raise NotImplementedError("TODO: implement ask_rag_stream")
