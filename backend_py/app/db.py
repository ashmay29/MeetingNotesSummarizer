import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None

MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/meeting-notes-summarizer")
DB_NAME = os.getenv("MONGO_DB", "meeting-notes-summarizer")

async def connect_db():
    global _client, _db
    if _client is not None:
        return
    _client = AsyncIOMotorClient(MONGO_URI)
    # Avoid boolean evaluation of Database objects; handle absence of default db
    try:
        default_db = _client.get_default_database()
    except Exception:
        default_db = None
    _db = default_db if default_db is not None else _client[DB_NAME]

async def close_db():
    global _client
    if _client is not None:
        _client.close()
        _client = None

def db() -> AsyncIOMotorDatabase:
    assert _db is not None, "DB not initialized"
    return _db
