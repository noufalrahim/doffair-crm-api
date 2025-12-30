from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine
from typing import Optional

from core.config import settings

_client: Optional[AsyncIOMotorClient] = None
_engine: Optional[AIOEngine] = None


def get_motor_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            uuidRepresentation="standard",
        )
    return _client


def get_engine() -> AIOEngine:
    global _engine
    if _engine is None:
        client = get_motor_client()
        _engine = AIOEngine(
            client=client,
            database=settings.MONGODB_DB_NAME,
        )
    return _engine
