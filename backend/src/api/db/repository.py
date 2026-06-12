"""
db/repository.py — Generic MongoDB repository
================================================
Thin generic CRUD wrapper around ``pymongo.collection.Collection``.

Designed for low memory:
    - Single repository instance per collection (reused across requests).
    - No identity map — objects are plain dicts/dataclasses.
    - All write operations are upsert-friendly.

Usage:
    from src.api.db.database import get_database
    db = get_database()
    users = Repository[User]("users", User, db)
    user = await users.find_one({"email": "a@b.com"})
    await users.insert_one(User(email="a@b.com", ...))
"""

import logging
from typing import TypeVar, Generic, Type, Optional

from pymongo.database import Database

from src.api.db.models import _new_id

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Repository(Generic[T]):
    """
    Generic repository for a single MongoDB collection.

    Parameters
    ----------
    collection_name : str
        Name of the MongoDB collection.
    model_class : Type[T]
        The dataclass type used to hydrate documents.
    database : Database, optional
        A pymongo Database instance.  If not provided, will attempt to
        resolve from the global connection.
    """

    def __init__(
        self,
        collection_name: str,
        model_class: Type[T],
        database: Optional[Database] = None,
    ):
        self.collection_name = collection_name
        self.model_class = model_class
        self._collection = None
        self._database = database
        if database is not None:
            self._collection = database[collection_name]

    # ── Connection ────────────────────────────────────────────────────────────

    def _get_collection(self):
        """Lazy-accessor for the PyMongo collection."""
        if self._collection is not None:
            return self._collection
        from src.api.db.database import get_database
        db = get_database()
        if db is None:
            raise RuntimeError(
                "MongoDB is not connected. Check your MONGO_URI setting."
            )
        self._collection = db[self.collection_name]
        return self._collection

    # ── CRUD ──────────────────────────────────────────────────────────────────

    async def find_one(self, filter: dict) -> Optional[T]:
        """
        Find a single document matching ``filter``.

        Example:
            user = await users.find_one({"email": "a@b.com"})
        """
        try:
            doc = self._get_collection().find_one(filter)
            return self.model_class.from_dict(doc) if doc else None  # type: ignore
        except Exception as exc:
            logger.error("find_one(%s) failed: %s", filter, exc)
            return None

    async def find_many(
        self,
        filter: dict,
        sort: Optional[list[tuple[str, int]]] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[T]:
        """
        Find documents matching ``filter`` with pagination.

        Example:
            convos = await conversations.find_many(
                {"user_id": uid}, sort=[("updated_at", -1)], limit=20
            )
        """
        try:
            cursor = self._get_collection().find(filter)
            if sort:
                cursor = cursor.sort(sort)
            return [self.model_class.from_dict(d) for d in cursor.skip(skip).limit(limit)]  # type: ignore
        except Exception as exc:
            logger.error("find_many(%s) failed: %s", filter, exc)
            return []

    async def count(self, filter: dict) -> int:
        """Count documents matching ``filter``."""
        try:
            return self._get_collection().count_documents(filter)
        except Exception as exc:
            logger.error("count(%s) failed: %s", filter, exc)
            return 0

    async def insert_one(self, model: T) -> str:
        """
        Insert a new document. Returns its ``_id`` string.

        Example:
            new_id = await users.insert_one(new_user)
        """
        try:
            doc = model.to_dict()  # type: ignore
            result = self._get_collection().insert_one(doc)
            return str(result.inserted_id)
        except Exception as exc:
            logger.error("insert_one failed: %s", exc)
            raise

    async def update_one(
        self, filter: dict, update: dict, upsert: bool = False
    ) -> bool:
        """
        Update one document matching ``filter``.
        Returns True if a document was modified/inserted.

        Example:
            await users.update_one(
                {"_id": uid},
                {"$set": {"display_name": "New Name"}}
            )
        """
        try:
            result = self._get_collection().update_one(filter, update, upsert=upsert)
            return result.modified_count > 0 or result.upserted_id is not None
        except Exception as exc:
            logger.error("update_one(%s) failed: %s", filter, exc)
            return False

    async def delete_one(self, filter: dict) -> bool:
        """Delete one document matching ``filter``. Returns True if deleted."""
        try:
            result = self._get_collection().delete_one(filter)
            return result.deleted_count > 0
        except Exception as exc:
            logger.error("delete_one(%s) failed: %s", filter, exc)
            return False

    async def aggregate(self, pipeline: list[dict]) -> list[dict]:
        """Run an aggregation pipeline."""
        try:
            return list(self._get_collection().aggregate(pipeline))
        except Exception as exc:
            logger.error("aggregate failed: %s", exc)
            return []

    async def create_index(self, keys: list[tuple[str, int]], **kwargs):
        """Create an index on the collection."""
        try:
            self._get_collection().create_index(keys, **kwargs)
        except Exception as exc:
            logger.error("create_index(%s) failed: %s", keys, exc)
