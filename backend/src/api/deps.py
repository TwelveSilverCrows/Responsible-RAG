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
    - ``get_db`` — yields a MongoDB database instance (TODO)
"""

from functools import lru_cache
from fastapi import Request
from src.core.config import Settings, get_settings

# Re-export for convenience
__all__ = ["get_settings", "get_rag_chain", "get_db"]


# Sentinel object to detect "not yet loaded"
_UNSET = object()
_rag_chain = _UNSET  # type: ignore


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


async def get_db():
    """
    Dependency that provides a MongoDB database instance.

    The connection is created once and reused via a connection pool
    (``maxPoolSize=2`` keeps memory low).

    Usage:
        async def my_handler(db = Depends(get_db)):
            collection = db["users"]
            ...

    TODO:
        - Create a single ``MongoClient`` in the lifespan handler.
        - Store it in ``app.state``.
        - Retrieve it here with ``request.app.state.db``.
    """
    # from motor.motor_asyncio import AsyncIOMotorClient
    # client = AsyncIOMotorClient(settings.mongo_uri, maxPoolSize=2)
    # db = client[settings.mongo_db]
    # return db
    raise NotImplementedError(
        "TODO: initialise MongoDB in lifespan handler and pass "
        "the database instance through app.state."
    )


# Re-export the cached settings getter from config
get_settings = get_settings
