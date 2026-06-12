"""
embeddings.py — Embedding-model factory (Hugging Face Inference API)
=====================================================================
Uses ``langchain_huggingface.HuggingFaceEndpointEmbeddings`` to call the
Hugging Face Inference API for feature extraction — no local GPU or heavy
dependency (torch / optimum / openvino) required.

The default model is ``BAAI/bge-large-en-v1.5``, the same model previously
used with the OpenVINO local backend.

Usage
-----
    from src.core.config import get_settings
    from src.core.embeddings import EmbeddingFactory

    embeddings = EmbeddingFactory.create(get_settings())
"""

import logging

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from src.core.config import Settings

logger = logging.getLogger(__name__)

# Type alias so callers can annotate without importing the class directly
EmbeddingModel = HuggingFaceEndpointEmbeddings


class EmbeddingFactory:
    """Creates a :class:`HuggingFaceEndpointEmbeddings` from settings."""

    @staticmethod
    def create(settings: Settings) -> HuggingFaceEndpointEmbeddings:
        """
        Return an embedding model that calls the Hugging Face Inference API.

        Parameters
        ----------
        settings:
            Application settings — must include ``huggingfacehub_api_token``
            and ``embedding_model``.

        Returns
        -------
        HuggingFaceEndpointEmbeddings
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
        return HuggingFaceEndpointEmbeddings(
            model=settings.embedding_model,
            task="feature-extraction",
            huggingfacehub_api_token=token,
        )
