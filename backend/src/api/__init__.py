"""
api/__init__.py — FastAPI application factory
==============================================
Usage:
    from src.api import create_app
    app = create_app()

This factory builds the FastAPI app, registers routers, and sets up
lifespan handlers for startup/shutdown.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan handler for startup / shutdown.

    Startup:
        - Connect to MongoDB (single connection pool, maxPoolSize=2).
        - (Optional) pre-warm the RAG chain (increases memory at startup).

    Shutdown:
        - Close MongoDB connection.
        - Release RAG chain resources.

    Example
    -------
        from motor.motor_asyncio import AsyncIOMotorClient
        from src.core.config import get_settings

        async with lifespan(app):
            settings = get_settings()
            # app.state.db = AsyncIOMotorClient(
            #     settings.mongo_uri, maxPoolSize=2
            # )[settings.mongo_db]
            yield
            # app.state.db.client.close()
    """
    # ── Startup ───────────────────────────────────────────────────────────────
    # TODO: Connect to MongoDB here (single connection for the app lifetime)
    # settings = get_settings()
    # app.state.mongo_client = AsyncIOMotorClient(settings.mongo_uri, maxPoolSize=2)
    # app.state.db = app.state.mongo_client[settings.mongo_db]
    yield
    # ── Shutdown ──────────────────────────────────────────────────────────────
    # TODO: Close connections
    # if hasattr(app.state, "mongo_client"):
    #     app.state.mongo_client.close()


def create_app() -> FastAPI:
    """
    Build and return a configured FastAPI application instance.

    Returns
    -------
    FastAPI
        The fully configured application.
    """
    app = FastAPI(
        title="Responsible RAG API",
        description=(
            "Retrieval-Augmented Generation service with audience-aware "
            "profiles, user management, consent, and admin features."
        ),
        version="0.2.0",
        lifespan=lifespan,
        # Low-memory: disable docs in production
        # docs_url=None,
        # redoc_url=None,
    )

    # ── Middleware ────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(api_router, prefix="/api/v1")

    # ── Root redirect → Swagger docs (dev convenience) ────────────────────────
    from fastapi.responses import RedirectResponse

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs")

    return app
