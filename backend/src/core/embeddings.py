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
import math

from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEndpointEmbeddings

from src.core.config import Settings
from src.core.embedding_quota import EmbeddingCooldownError, get_quota_monitor

logger = logging.getLogger(__name__)

# Type alias so callers can annotate without importing the class directly
EmbeddingModel = HuggingFaceEndpointEmbeddings


# ═══════════════════════════════════════════════════════════════════════════════
# Embedding validation
# ═══════════════════════════════════════════════════════════════════════════════


class EmbeddingValidationError(RuntimeError):
    """Raised when an embedding vector fails validation (corrupted)."""


def validate_embedding(embedding: list[float], label: str = "embedding") -> None:
    """
    Validate a single embedding vector for corruption.

    Checks:
    - Not empty
    - No NaN or infinity values
    - Not all zeros (typically indicates a silent failure)

    Raises :class:`EmbeddingValidationError` if the vector is corrupted.
    """
    if not embedding:
        raise EmbeddingValidationError(f"{label} is empty")

    if all(v == 0.0 for v in embedding):
        raise EmbeddingValidationError(f"{label} is all zeros — possible API failure")

    for i, v in enumerate(embedding):
        if math.isnan(v):
            raise EmbeddingValidationError(f"{label} contains NaN at index {i}")
        if math.isinf(v):
            raise EmbeddingValidationError(f"{label} contains infinity at index {i}")


def validate_embeddings(
    embeddings: list[list[float]],
    expected_dim: int | None = None,
) -> None:
    """
    Validate a batch of embedding vectors.

    Parameters
    ----------
    embeddings:
        The list of embedding vectors to validate.
    expected_dim:
        If set, every vector must have exactly this many dimensions.
    """
    if not embeddings:
        raise EmbeddingValidationError("embedding batch is empty")

    for i, emb in enumerate(embeddings):
        validate_embedding(emb, label=f"embedding[{i}]")

    if expected_dim is not None:
        for i, emb in enumerate(embeddings):
            if len(emb) != expected_dim:
                raise EmbeddingValidationError(
                    f"embedding[{i}] has {len(emb)} dimensions, "
                    f"expected {expected_dim}"
                )


# ═══════════════════════════════════════════════════════════════════════════════
# Quota-aware wrapper
# ═══════════════════════════════════════════════════════════════════════════════


class QuotaAwareEmbeddings(Embeddings):
    """
    Wraps a LangChain-compatible ``Embeddings`` instance with quota monitoring
    and embedding validation.

    Every ``embed_documents`` / ``embed_query`` call is guarded by:
    1. A cooldown check — if the API is in cooldown, an
       :class:`EmbeddingCooldownError` is raised immediately.
    2. Error interception — any exception raised by the underlying embeddings
       is inspected; quota-related errors trigger a cooldown.
    3. Validation — the returned vectors are checked for NaN, infinity,
       and all-zero patterns that indicate a corrupted result.

    Parameters
    ----------
    embeddings:
        The underlying LangChain ``Embeddings`` instance to wrap.
    """

    def __init__(self, embeddings: Embeddings) -> None:
        self._embeddings = embeddings
        self._monitor = get_quota_monitor()
        # Expected dimension — learned from the first successful embedding call
        self._expected_dim: int | None = None

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents, respecting any active cooldown."""
        if self._monitor.is_in_cooldown():
            raise EmbeddingCooldownError(
                f"Embedding API is in cooldown for another "
                f"{self._monitor.get_cooldown_remaining():.0f}s. "
                f"Try again later."
            )
        try:
            result = self._embeddings.embed_documents(texts)
            self._validate_and_learn_dim(result)
            return result
        except EmbeddingValidationError:
            raise
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
            result = self._embeddings.embed_query(text)
            validate_embedding(result, label="query_embedding")
            if self._expected_dim is None:
                self._expected_dim = len(result)
            return result
        except EmbeddingValidationError:
            raise
        except Exception as exc:
            self._monitor.record_error(exc)
            raise

    def _validate_and_learn_dim(self, embeddings: list[list[float]]) -> None:
        """Validate a batch and learn the expected dimension from the first call."""
        validate_embeddings(embeddings, expected_dim=self._expected_dim)
        if self._expected_dim is None and embeddings:
            self._expected_dim = len(embeddings[0])
            logger.debug("Learned expected embedding dimension: %d", self._expected_dim)


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
