from pymongo import MongoClient, ASCENDING
from app.config import settings

client = MongoClient(settings.MONGO_URI)
db = client[settings.DB_NAME]
users_collection = db["users"]


def init_indexes() -> None:
    """Call once at startup when Mongo is reachable."""
    users_collection.create_index([("email", ASCENDING)], unique=True)
