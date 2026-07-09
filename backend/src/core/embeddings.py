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

class OpenVINOEmbeddings(Embeddings):
    """Calls the local OpenVINO server optimized for Intel Xeon."""
    
    def __init__(self, api_url: str) -> None:
        self.api_url = api_url

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts: return []
        resp = httpx.post(
            self.api_url, 
            json={"texts": texts, "is_query": False}, 
            timeout=60.0 
        )
        resp.raise_for_status()
        return resp.json()["embeddings"]

    def embed_query(self, text: str) -> list[float]:
        resp = httpx.post(
            self.api_url, 
            json={"texts": [text], "is_query": True}, 
            timeout=60.0 
        )
        resp.raise_for_status()
        return resp.json()["embeddings"][0]
    

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
    """Creates an embedding client from settings (OpenVINO or HF Inference API)."""

    @staticmethod
    def create(settings: Settings) -> Embeddings:
        provider = settings.embedding_provider
        if provider == "openvino":
            url = settings.local_embedding_url
            if not url:
                raise RuntimeError(
                    "LOCAL_EMBEDDING_URL is not set. Add it to your .env file."
                )
            logger.info("Using OpenVINO server (url=%s)", url)
            return OpenVINOEmbeddings(api_url=url)

        # Fallback: Hugging Face Inference API
        token = settings.huggingfacehub_api_token
        if not token:
            raise RuntimeError(
                "HUGGINGFACEHUB_API_TOKEN is not set. Add it to your .env file."
            )
        logger.info("Using HF Inference API (model=%s)", settings.embedding_model)
        return HFInferenceEmbeddings(model=settings.embedding_model, token=token)
