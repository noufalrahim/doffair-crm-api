from odmantic import AIOEngine
from bson import ObjectId
from datetime import datetime
from fastapi import HTTPException
from typing import List, Optional

from vendor.models.store_item import StoreItem
from vendor.schemas.store_item import StoreItemCreate, StoreItemUpdate

async def create_store_item(engine: AIOEngine, vendor_id: str, data: StoreItemCreate) -> StoreItem:
    store_item = StoreItem(
        vendor_id=vendor_id,
        **data.model_dump()
    )
    await engine.save(store_item)
    return store_item

async def get_store_item_by_id(engine: AIOEngine, vendor_id: str, item_id: str) -> StoreItem:
    store_item = await engine.find_one(StoreItem, StoreItem.id == ObjectId(item_id), StoreItem.vendor_id == vendor_id)
    if not store_item:
        raise HTTPException(status_code=404, detail="Store item not found")
    return store_item

async def list_store_items(
    engine: AIOEngine, 
    vendor_id: str, 
    vertical_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    category: Optional[str] = None
) -> List[StoreItem]:
    query = [StoreItem.vendor_id == vendor_id]
    if vertical_id:
        query.append(StoreItem.vertical_id == vertical_id)
    if is_active is not None:
        query.append(StoreItem.is_active == is_active)
    if category:
        query.append(StoreItem.category == category)
    if search:
        query.append(StoreItem.name.match(f"(?i).*{search}.*"))
    
    store_items = await engine.find(StoreItem, *query)
    return store_items

async def update_store_item(engine: AIOEngine, vendor_id: str, item_id: str, data: StoreItemUpdate) -> StoreItem:
    store_item = await get_store_item_by_id(engine, vendor_id, item_id)
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(store_item, key, value)
    
    store_item.updated_at = datetime.utcnow()
    await engine.save(store_item)
    return store_item

async def delete_store_item(engine: AIOEngine, vendor_id: str, item_id: str) -> bool:
    store_item = await get_store_item_by_id(engine, vendor_id, item_id)
    await engine.delete(store_item)
    return True

async def bulk_create_store_items(engine: AIOEngine, vendor_id: str, items_data: List[dict]) -> List[StoreItem]:
    """
    Bulk create store items.
    """
    items = []
    for data in items_data:
        it = StoreItem(
            vendor_id=vendor_id,
            **data
        )
        items.append(it)
    
    if items:
        for it in items:
            await engine.save(it)
            
    return items
