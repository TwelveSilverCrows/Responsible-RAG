"""
embeddings.py — Embedding-model factory (Hugging Face Inference API)
=====================================================================
Lightweight client that calls the HF Inference API via ``httpx`` — no
local GPU, torch, or transformers dependency required.

Usage
-----
    from src.core.config import get_settings
    from src.core.embeddings import EmbeddingFactory

    embeddings = EmbeddingFactory.create(get_settings())
"""

import logging
import math
import threading

import httpx
from langchain_core.embeddings import Embeddings

from src.core.config import Settings

logger = logging.getLogger(__name__)


class EmbeddingValidationError(RuntimeError):
    """Raised when an embedding vector fails validation (corrupted)."""


def validate_embedding(embedding: list[float], label: str = "embedding") -> None:
    """Validate a single embedding vector for corruption."""
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
    """Validate a batch of embedding vectors."""
    if not embeddings:
        raise EmbeddingValidationError("embedding batch is empty")
    for i, emb in enumerate(embeddings):
        validate_embedding(emb, label=f"embedding[{i}]")
    if expected_dim is not None:
        for i, emb in enumerate(embeddings):
            if len(emb) != expected_dim:
                raise EmbeddingValidationError(
                    f"embedding[{i}] has {len(emb)} dimensions, expected {expected_dim}"
                )

class TEIEmbeddings(Embeddings):
    """Calls Hugging Face Text Embeddings Inference (TEI) server.

    - Limits concurrent requests to avoid overwhelming the server
    - Retries on 429 rate-limits with exponential backoff
    """

    def __init__(
        self,
        api_url: str,
        max_concurrency: int = 2,
        max_retries: int = 8,
    ) -> None:
        self.api_url = api_url
        self.max_retries = max_retries
        self._semaphore = threading.Semaphore(max_concurrency)

    def _call(self, payload: dict) -> list | list[list]:
        """POST to TEI with concurrency limiting and retry on 429."""
        import random as _random
        import time as _time

        with self._semaphore:
            for attempt in range(self.max_retries):
                resp = httpx.post(
                    self.api_url,
                    json=payload,
                    timeout=300.0,
                )
                if resp.status_code == 429 and attempt < self.max_retries - 1:
                    base = 2 ** attempt
                    jitter = _random.uniform(0, base)
                    wait = base + jitter
                    logger.warning(
                        "TEI rate-limited (429), retrying in %.1fs (attempt %d/%d)",
                        wait, attempt + 1, self.max_retries,
                    )
                    _time.sleep(wait)
                    continue
                resp.raise_for_status()
                return resp.json()
        raise RuntimeError("TEI request failed after max retries")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        # Split into sub-batches of 32 to avoid TEI's batch size limit
        batch_size = 32
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            all_embeddings.extend(self._call({"inputs": batch, "normalize": True}))
        return all_embeddings

    def embed_query(self, text: str) -> list[float]:
        # TEI always returns [[float]] — unwrap the single result
        return self._call({"inputs": text, "normalize": True})[0]


class HFInferenceEmbeddings(Embeddings):
    """Lightweight Hugging Face Inference API client for feature extraction.

    Replaces ``langchain_huggingface.HuggingFaceEndpointEmbeddings`` to avoid
    importing torch/transformers (which add 10-15s to startup).

    For BGE-family models (BAAI/bge-*) the constructor automatically applies
    the standard BGE instruction prefixes to ensure compatibility with
    ``OpenVINOBgeEmbeddings`` used during KB building.
    """

    # BGE instruction prefixes — matches OpenVINOBgeEmbeddings defaults
    _QUERY_INSTRUCTION = "Represent this query for searching relevant passages: "
    _DOCUMENT_INSTRUCTION = "Represent this document for retrieval: "

    def __init__(self, model: str, token: str) -> None:
        self.model = model
        self.token = token
        # https://huggingface.co/docs/api-inference/en/getting-started
        self.api_url = f"https://router.huggingface.co/hf-inference/models/{model}"
        # BGE models need instruction prefixes for consistent embeddings
        self._is_bge = "bge" in model.lower()
        if self._is_bge:
            logger.info(
                "BGE model detected — applying instruction prefixes "
                "(query=%.40s… doc=%.40s…)",
                self._QUERY_INSTRUCTION, self._DOCUMENT_INSTRUCTION,
            )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if self._is_bge:
            texts = [f"{self._DOCUMENT_INSTRUCTION}{t}" for t in texts]
        resp = httpx.post(
            self.api_url,
            headers={"Authorization": f"Bearer {self.token}"},
            json={"inputs": texts, "options": {"wait_for_model": True}},
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()

    def embed_query(self, text: str) -> list[float]:
        if self._is_bge:
            text = f"{self._QUERY_INSTRUCTION}{text}"
        return self.embed_documents([text])[0]


class EmbeddingFactory:
    """Creates an embedding client from settings (TEI or HF Inference API)."""

    @staticmethod
    def create(settings: Settings) -> Embeddings:
        provider = settings.embedding_provider
        if provider == "tei":
            url = settings.local_embedding_url
            if not url:
                raise RuntimeError(
                    "LOCAL_EMBEDDING_URL is not set. Add it to your .env file."
                )
            logger.info("Using TEI server (url=%s)", url)
            return TEIEmbeddings(api_url=url)

        # Fallback: Hugging Face Inference API
        token = settings.huggingfacehub_api_token
        if not token:
            raise RuntimeError(
                "HUGGINGFACEHUB_API_TOKEN is not set. Add it to your .env file."
            )
        logger.info("Using HF Inference API (model=%s)", settings.embedding_model)
        return HFInferenceEmbeddings(model=settings.embedding_model, token=token)
