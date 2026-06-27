"""
api/deps.py — Dependency injection
=====================================
FastAPI dependencies that provide shared resources to route handlers.

Low-memory strategy:
    - RAG chain is a **lazy singleton** — loaded on first request, cached
      for subsequent ones. This avoids loading the embedding model at import
      time.
    - Use ``@lru_cache(1)`` or a module-level variable with a sentinel.
    - Each dependency is a generator so FastAPI can manage cleanup via
      ``yield`` (e.g. release model memory on app shutdown).

Available dependencies:
    - ``get_settings`` — cached Settings singleton (from src.core.config)
    - ``get_rag_chain`` — lazy-loaded RAGChain singleton
    - ``get_profile_generator`` — lazy-loaded ProfileGeneratorService singleton
"""

from src.core.config import Settings, get_settings

# Re-export for convenience
__all__ = ["get_settings", "get_rag_chain", "get_profile_generator"]


# Sentinel object to detect "not yet loaded"
_UNSET = object()
_rag_chain = _UNSET  # type: ignore
_profile_generator = _UNSET  # type: ignore


async def get_rag_chain():
    """
    Dependency that provides a lazily-loaded, cached RAGChain instance.

    The chain (including embedding model, vector store, retriever, and LLM)
    is built only once and reused across all requests. This is critical for
    low-memory environments — building the chain requires loading large
    models into RAM.

    Usage:
        async def my_handler(chain = Depends(get_rag_chain)):
            result = chain.invoke("...")

    Returns
    -------
    RAGChain
        The singleton RAG chain instance.
    """
    global _rag_chain

    if _rag_chain is _UNSET:
        # Lazy initialisation — only runs on the first request
        from src.core.rag_chain import RAGChain

        settings = get_settings()
        _rag_chain = RAGChain(settings)

    return _rag_chain


async def get_profile_generator():
    """
    Dependency that provides a lazily-loaded, cached ProfileGeneratorService.

    The service wraps ``ProfileAugmenter`` which loads the profiles vector
    store (``vectordb_profiles/``) and its embedding model on first use.

    Usage:
        async def my_handler(gen = Depends(get_profile_generator)):
            prompt = gen.generate_prompt(user_profile={...}, user_query=...)

    Returns
    -------
    ProfileGeneratorService
        The singleton profile generator service.
    """
    global _profile_generator

    if _profile_generator is _UNSET:
        from src.api.services.profile_generator_service import (
            ProfileGeneratorService,
        )

        _profile_generator = ProfileGeneratorService()

    return _profile_generator


# Re-export the cached settings getter from config
get_settings = get_settings
