"""
db/repository.py — Generic MongoDB repository
================================================
Thin generic CRUD wrapper around ``pymongo.collection.Collection``.

Designed for low memory:
    - Single repository instance per collection (reused across requests).
    - No identity map — objects are plain dicts/dataclasses.
    - All write operations are upsert-friendly.

Usage:
    users = Repository[User]("users", User)
    user = await users.find_one({"email": "a@b.com"})
    await users.insert_one(User(email="a@b.com", ...))

TODOs for real implementation:
    - Replace ``mongomock`` with real ``pymongo`` in production.
    - Add ``create_index(...)`` helpers.
    - Add aggregation pipeline support.
"""

from dataclasses import dataclass
from typing import (
    TypeVar,
    Generic,
    Type,
    Optional,
    Any,
)
from src.api.db.models import _new_id


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
    """

    def __init__(self, collection_name: str, model_class: Type[T]):
        self.collection_name = collection_name
        self.model_class = model_class
        # TODO: Inject a real pymongo.db.Database instance from a connection pool
        # self._collection = db[collection_name]
        self._collection = None  # placeholder

    # ── Connection (stub) ─────────────────────────────────────────────────────

    def _get_collection(self):
        """
        Lazy-accessor for the PyMongo collection.
        Implementations should connect from a pool on first call.
        """
        # TODO: Replace with real pymongo:
        # if self._collection is None:
        #     from pymongo import MongoClient
        #     client = MongoClient(settings.mongo_uri, maxPoolSize=2)
        #     self._collection = client[settings.mongo_db][self.collection_name]
        # return self._collection
        raise NotImplementedError(
            "Connect to MongoDB in your app's lifespan handler and "
            "pass the database instance to Repository."
        )

    # ── CRUD ──────────────────────────────────────────────────────────────────

    async def find_one(self, filter: dict) -> Optional[T]:
        """
        Find a single document matching ``filter``.

        Example:
            user = await users.find_one({"email": "a@b.com"})
        """
        # doc = self._get_collection().find_one(filter)
        # return self.model_class.from_dict(doc) if doc else None
        raise NotImplementedError("TODO: implement with pymongo")

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
        # cursor = self._get_collection().find(filter)
        # if sort:
        #     cursor = cursor.sort(sort)
        # return [self.model_class.from_dict(d) for d in cursor.skip(skip).limit(limit)]
        raise NotImplementedError("TODO: implement with pymongo")

    async def count(self, filter: dict) -> int:
        """Count documents matching ``filter``."""
        # return self._get_collection().count_documents(filter)
        raise NotImplementedError("TODO: implement with pymongo")

    async def insert_one(self, model: T) -> str:
        """
        Insert a new document. Returns its ``_id`` string.

        Example:
            new_id = await users.insert_one(new_user)
        """
        # doc = model.to_dict()
        # result = self._get_collection().insert_one(doc)
        # return str(result.inserted_id)
        raise NotImplementedError("TODO: implement with pymongo")

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
        # result = self._get_collection().update_one(filter, update, upsert=upsert)
        # return result.modified_count > 0 or result.upserted_id is not None
        raise NotImplementedError("TODO: implement with pymongo")

    async def delete_one(self, filter: dict) -> bool:
        """Delete one document matching ``filter``. Returns True if deleted."""
        # result = self._get_collection().delete_one(filter)
        # return result.deleted_count > 0
        raise NotImplementedError("TODO: implement with pymongo")

    async def aggregate(self, pipeline: list[dict]) -> list[dict]:
        """Run an aggregation pipeline."""
        # return list(self._get_collection().aggregate(pipeline))
        raise NotImplementedError("TODO: implement with pymongo")
