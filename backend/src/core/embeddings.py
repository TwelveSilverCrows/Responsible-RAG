"""
embeddings.py — Embedding-model factory (Hugging Face Inference API)
=====================================================================
Uses ``langchain_huggingface.HuggingFaceEndpointEmbeddings`` to call the
Hugging Face Inference API for feature extraction — no local GPU or heavy
dependency (torch / optimum / openvino) required.

The default model is ``BAAI/bge-large-en-v1.5``, the same model previously
used with the OpenVINO local backend.

The returned embeddings instance is wrapped with
:class:`QuotaAwareEmbeddings` so that quota / rate-limit errors from the
HuggingFace API are caught and trigger a cooldown period rather than
breaking the application.

Usage
-----
    from src.core.config import get_settings
    from src.core.embeddings import EmbeddingFactory

    embeddings = EmbeddingFactory.create(get_settings())
"""

import logging

from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEndpointEmbeddings

from src.core.config import Settings
from src.core.embedding_quota import EmbeddingCooldownError, get_quota_monitor

logger = logging.getLogger(__name__)

# Type alias so callers can annotate without importing the class directly
EmbeddingModel = HuggingFaceEndpointEmbeddings


# ═══════════════════════════════════════════════════════════════════════════════
# Quota-aware wrapper
# ═══════════════════════════════════════════════════════════════════════════════


class QuotaAwareEmbeddings(Embeddings):
    """
    Wraps a LangChain-compatible ``Embeddings`` instance with quota monitoring.

    Every ``embed_documents`` / ``embed_query`` call is guarded by:
    1. A cooldown check — if the API is in cooldown, an
       :class:`EmbeddingCooldownError` is raised immediately.
    2. Error interception — any exception raised by the underlying embeddings
       is inspected; quota-related errors trigger a cooldown.

    Parameters
    ----------
    embeddings:
        The underlying LangChain ``Embeddings`` instance to wrap.
    """

    def __init__(self, embeddings: Embeddings) -> None:
        self._embeddings = embeddings
        self._monitor = get_quota_monitor()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents, respecting any active cooldown."""
        if self._monitor.is_in_cooldown():
            raise EmbeddingCooldownError(
                f"Embedding API is in cooldown for another "
                f"{self._monitor.get_cooldown_remaining():.0f}s. "
                f"Try again later."
            )
        try:
            return self._embeddings.embed_documents(texts)
        except Exception as exc:
            self._monitor.record_error(exc)
            raise

    def embed_query(self, text: str) -> list[float]:
        """Embed a query string, respecting any active cooldown."""
        if self._monitor.is_in_cooldown():
            raise EmbeddingCooldownError(
                f"Embedding API is in cooldown for another "
                f"{self._monitor.get_cooldown_remaining():.0f}s. "
                f"Try again later."
            )
        try:
            return self._embeddings.embed_query(text)
        except Exception as exc:
            self._monitor.record_error(exc)
            raise


# ═══════════════════════════════════════════════════════════════════════════════
# Factory
# ═══════════════════════════════════════════════════════════════════════════════


class EmbeddingFactory:
    """Creates a quota-aware :class:`HuggingFaceEndpointEmbeddings` from settings."""

    @staticmethod
    def create(settings: Settings) -> QuotaAwareEmbeddings:
        """
        Return an embedding model that calls the Hugging Face Inference API.

        The returned instance is wrapped with :class:`QuotaAwareEmbeddings`
        so that quota / rate-limit errors are caught and trigger a cooldown
        rather than propagating as 500 errors.

        Parameters
        ----------
        settings:
            Application settings — must include ``huggingfacehub_api_token``
            and ``embedding_model``.

        Returns
        -------
        QuotaAwareEmbeddings
        """
        token = settings.huggingfacehub_api_token
        if not token:
            raise RuntimeError(
                "HUGGINGFACEHUB_API_TOKEN is not set. "
                "Add it to your .env file or export the environment variable."
            )

        logger.info(
            "Using Hugging Face Inference API (model=%s, task=feature-extraction)",
            settings.embedding_model,
        )
        raw = HuggingFaceEndpointEmbeddings(
            model=settings.embedding_model,
            task="feature-extraction",
            huggingfacehub_api_token=token,
        )
        return QuotaAwareEmbeddings(raw)
