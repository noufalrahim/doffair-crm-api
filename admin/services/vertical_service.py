from odmantic import AIOEngine
from fastapi import HTTPException, status
from bson import ObjectId
from typing import List, Optional

from datetime import datetime
from admin.models.vertical import Vertical
from admin.schemas.vertical import VerticalCreate, VerticalUpdate


async def create_vertical(
    engine: AIOEngine,
    payload: VerticalCreate,
) -> Vertical:
    # Check if ANY of the codes in the list already exist
    existing = await engine.find_one(
        Vertical,
        {"code": {"$in": payload.code}}
    )
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="One or more codes already exist in a vertical",
        )

    vertical = Vertical(
        code=payload.code,
        display_name=payload.display_name,
        description=payload.description,
        mode=payload.mode,
        url=payload.url,
        icon=payload.icon,
        priority=payload.priority,
    )

    await engine.save(vertical)
    return vertical


async def get_vertical_by_id(
    engine: AIOEngine,
    vertical_id: str,
) -> Vertical:
    try:
        oid = ObjectId(vertical_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vertical id format",
        )
    
    vertical = await engine.find_one(Vertical, Vertical.id == oid)
    if not vertical:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vertical not found",
        )
    return vertical


async def list_verticals(
    engine: AIOEngine,
    include_inactive: bool = True,
) -> List[Vertical]:
    if include_inactive:
        return await engine.find(Vertical)
    return await engine.find(Vertical, Vertical.is_active == True)


async def update_vertical(
    engine: AIOEngine,
    vertical_id: str,
    payload: VerticalUpdate,
) -> Vertical:
    vertical = await get_vertical_by_id(engine, vertical_id)

    update_data = payload.model_dump(exclude_unset=True)
    
    if "code" in update_data:
        # Check if new codes conflict with existing verticals (excluding self)
        existing = await engine.find_one(
            Vertical,
            {
                "_id": {"$ne": vertical.id},
                "code": {"$in": update_data["code"]}
            }
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="One or more codes already exist in another vertical",
            )

    for field, value in update_data.items():
        setattr(vertical, field, value)

    vertical.updated_at = datetime.utcnow()
    await engine.save(vertical)
    return vertical


async def toggle_vertical_status(
    engine: AIOEngine,
    vertical_id: str,
    is_active: bool,
) -> Vertical:
    vertical = await get_vertical_by_id(engine, vertical_id)
    vertical.is_active = is_active
    vertical.updated_at = datetime.utcnow()
    await engine.save(vertical)
    return vertical


async def delete_vertical(
    engine: AIOEngine,
    vertical_id: str,
) -> bool:
    vertical = await get_vertical_by_id(engine, vertical_id)
    await engine.delete(vertical)
    return True
