"""
db/database.py — MongoDB connection management
=================================================
Manages a single ``pymongo.MongoClient`` instance for the application
lifetime.  The client is created in the FastAPI lifespan handler and
stored in ``app.state``.

Usage:
    from src.api.db.database import get_db, close_db

    # In lifespan handler:
    await get_db()
    yield
    close_db()

    # In route handlers (via Depends):
    db = await get_db()  # returns the cached MongoClient
"""

import logging
from typing import Optional

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from src.core.config import get_settings

logger = logging.getLogger(__name__)

_client: Optional[MongoClient] = None


async def get_db():
    """
    Return the application's cached MongoDB client.

    Creates the client on first call (lazy initialisation).
    The client uses ``maxPoolSize=2`` for low-memory operation.

    Returns
    -------
    pymongo.MongoClient
        The MongoDB client, or ``None`` if not configured.
    """
    global _client

    if _client is not None:
        return _client

    settings = get_settings()
    if not settings.mongo_uri:
        logger.warning("MONGO_URI not set — MongoDB features disabled.")
        return None

    try:
        _client = MongoClient(
            settings.mongo_uri,
            maxPoolSize=2,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        # Verify connection
        _client.admin.command("ping")
        logger.info("Connected to MongoDB at %s", settings.mongo_uri.replace(settings.mongo_uri.split("@")[0], "***"))
    except ConnectionFailure as exc:
        logger.error("Failed to connect to MongoDB: %s", exc)
        _client = None
        return None

    return _client


def get_database():
    """
    Get the configured database from the cached client.

    Returns
    -------
    pymongo.database.Database or None
    """
    client = _client
    if client is None:
        return None
    settings = get_settings()
    return client[settings.mongo_db]


def get_users_collection():
    """Get the users collection from the database."""
    db = get_database()
    if db is None:
        return None
    return db["users"]


def init_indexes():
    """Create indexes for MongoDB collections."""
    from pymongo import ASCENDING
    users = get_users_collection()
    if users is not None:
        users.create_index([("email", ASCENDING)], unique=True)
        db = users.database
        db["profiles"].create_index([("user_id", ASCENDING)], unique=True)
        db["consent"].create_index([("user_id", ASCENDING)], unique=True)
        logger.info("MongoDB indexes initialized.")


def close_db():
    """Close the MongoDB connection pool."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("MongoDB connection closed.")
