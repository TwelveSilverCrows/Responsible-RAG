"""
embeddings.py — Embedding-model factory
==========================================
Abstracts over two local embedding backends so that the rest of the codebase
never needs to know which one is active.

Supported backends
------------------
OpenVINO (auto-detected)
    ``BAAI/bge-large-en-v1.5`` compiled for Intel CPU / NPU / GPU via the
    OpenVINO runtime. Auto-detected when Intel hardware is available.

Nomic Embed (fallback)
    ``nomic-embed-text-v1.5`` running in local inference mode.
    Used when no Intel hardware is detected.

Usage
-----
    from src.core.config import get_settings
    from src.core.embeddings import EmbeddingFactory

    embeddings = EmbeddingFactory.create(get_settings())
"""

import logging
import sys
from typing import Union

from langchain_community.embeddings import OpenVINOEmbeddings
from langchain_nomic import NomicEmbeddings

from src.core.config import Settings

logger = logging.getLogger(__name__)

# Type alias for the union of supported embedding types
EmbeddingModel = Union[OpenVINOEmbeddings, NomicEmbeddings]


def _detect_intel_hardware() -> str | None:
    """
    Detect available Intel hardware and return the best device to use.

    Returns
    -------
    str | None
        Device string ('CPU', 'GPU', 'NPU') if Intel hardware detected,
        None if no Intel hardware available.
    """
    try:
        # Try to import openvino to check if it's available
        import openvino as ov

        # Get available devices
        available_devices = ov.Core().available_devices

        # Priority: NPU > GPU > CPU
        if "NPU" in available_devices:
            logger.info("Detected Intel NPU")
            return "NPU"
        if "GPU" in available_devices:
            logger.info("Detected Intel GPU")
            return "GPU"
        if "CPU" in available_devices:
            logger.info("Detected Intel CPU")
            return "CPU"

    except ImportError:
        logger.debug("OpenVINO not installed")
    except Exception as exc:
        logger.debug(f"Failed to detect Intel hardware: {exc}")

    return None


class EmbeddingFactory:
    """Static factory that instantiates the configured embedding model."""

    @staticmethod
    def create(settings: Settings) -> EmbeddingModel:
        """
        Return an embedding model instance based on *settings* and auto-detected hardware.

        Auto-detection priority:
        1. If USE_NOMIC explicitly set to true in settings → use Nomic
        2. If Intel hardware detected → use OpenVINO on best available device
        3. Otherwise → fall back to Nomic

        Parameters
        ----------
        settings:
            Application settings (see :class:`src.core.config.Settings`).

        Returns
        -------
        EmbeddingModel
            Either an :class:`OpenVINOEmbeddings` or :class:`NomicEmbeddings`
            instance, ready to call ``.embed_documents()`` / ``.embed_query()``.
        """
        # Explicit override: user wants Nomic
        if settings.use_nomic:
            logger.info(
                "Using Nomic embedding backend (explicitly configured, dimensionality=%d)",
                settings.nomic_dimensionality,
            )
            return NomicEmbeddings(
                model="nomic-embed-text-v1.5",
                dimensionality=settings.nomic_dimensionality,
                inference_mode="local",
            )

        # Auto-detect Intel hardware
        detected_device = _detect_intel_hardware()

        if detected_device:
            # Use detected device, respect user's normalize setting
            logger.info(
                "Using OpenVINO embedding backend (auto-detected device=%s, model=%s)",
                detected_device,
                settings.embedding_model,
            )
            return OpenVINOEmbeddings(
                model_name_or_path=settings.embedding_model,
                model_kwargs={"device": detected_device},
                encode_kwargs={"normalize_embeddings": settings.embedding_normalize},
            )

        # No Intel hardware detected → fall back to Nomic
        logger.info(
            "No Intel hardware detected, falling back to Nomic embedding backend (dimensionality=%d)",
            settings.nomic_dimensionality,
        )
        return NomicEmbeddings(
            model="nomic-embed-text-v1.5",
            dimensionality=settings.nomic_dimensionality,
            inference_mode="local",
        )
