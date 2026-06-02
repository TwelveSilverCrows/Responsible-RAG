"""
config.py — Application configuration
========================================
All runtime parameters are read from environment variables (or a .env file).
Change defaults here **or** override them per-environment via .env / Docker
environment injection — no code changes required.

Usage
-----
    from src.core.config import get_settings

    cfg = get_settings()          # cached singleton
    print(cfg.llm_model)
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings.

    All fields map 1-to-1 to an environment variable of the same name
    (case-insensitive).  See example.env for a fully annotated reference.
    """

    # ── LLM ───────────────────────────────────────────────────────────────────
    llm_model: str = "deepseek-chat"
    llm_temperature: float = 0.2
    deepseek_api_key: str = ""

    # ── Embeddings ────────────────────────────────────────────────────────────
    # Auto-detected: OpenVINO will auto-detect Intel CPU/NPU/GPU at runtime.
    # Set USE_NOMIC=true to force Nomic embedding backend instead.
    embedding_model: str = "BAAI/bge-large-en-v1.5"
    embedding_device: str = "CPU"          # Fallback if auto-detection fails
    embedding_normalize: bool = True
    use_nomic: bool = False                # Force Nomic (bypasses auto-detection)
    nomic_dimensionality: int = 512

    # ── Chunking ──────────────────────────────────────────────────────────────
    use_semantic_chunking: bool = True
    fallback_chunk_size: int = 1000
    chunk_overlap: int = 200
    max_chunk_size: int = 2000             # Semantic chunks larger than this
                                           # trigger recursive fallback

    # ── Retrieval ─────────────────────────────────────────────────────────────
    vec_retriever_k: int = 5
    bm25_retriever_k: int = 5
    vec_weight: float = 0.7                # Must sum to 1.0 with bm25_weight
    bm25_weight: float = 0.3

    # ── Storage paths ─────────────────────────────────────────────────────────
    chroma_persist_dir: str = "./chroma_db"
    resources_dir: str = "./resources"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",          # Silently ignore unknown env vars
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached, application-wide Settings singleton."""
    return Settings()
