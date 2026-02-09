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


_secondary_client: Optional[AsyncIOMotorClient] = None
_secondary_engine: Optional[AIOEngine] = None


def get_secondary_motor_client() -> AsyncIOMotorClient:
    global _secondary_client
    if _secondary_client is None:
        if not settings.MONGODB_URI_SECONDARY:
            raise ValueError("MONGODB_URI_SECONDARY is not set in configuration")
        _secondary_client = AsyncIOMotorClient(
            settings.MONGODB_URI_SECONDARY,
            uuidRepresentation="standard",
        )
    return _secondary_client


def get_secondary_engine() -> AIOEngine:
    global _secondary_engine
    if _secondary_engine is None:
        client = get_secondary_motor_client()
        _secondary_engine = AIOEngine(
            client=client,
            database=settings.MONGODB_DB_NAME_SECONDARY,
        )
    return _secondary_engine
