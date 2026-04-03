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
    category: Optional[str] = None,
    skip: int = 0,
    limit: Optional[int] = None
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
    
    store_items = await engine.find(StoreItem, *query, skip=skip, limit=limit, sort=StoreItem.created_at.desc())
    return store_items

async def count_store_items(
    engine: AIOEngine,
    vendor_id: str,
    vertical_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    category: Optional[str] = None
) -> int:
    query = [StoreItem.vendor_id == vendor_id]
    if vertical_id:
        query.append(StoreItem.vertical_id == vertical_id)
    if is_active is not None:
        query.append(StoreItem.is_active == is_active)
    if category:
        query.append(StoreItem.category == category)
    if search:
        query.append(StoreItem.name.match(f"(?i).*{search}.*"))
        
    count = await engine.count(StoreItem, *query)
    return count

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
    Bulk create store items with robustness for varied input data.
    Filters out invalid fields and skips empty/incomplete rows.
    """
    items = []
    
    # Identify valid model fields to prevent TypeError from unknown keys
    valid_fields = set(StoreItem.model_fields.keys())
    
    for data in items_data:
        try:
            # 1. Skip rows missing critical info (e.g., name)
            if not data.get("name"):
                print("DEBUG: Skipping store item row with missing name")
                continue
                
            # 2. Filter data to only include valid model fields
            filtered_data = {
                k: v for k, v in data.items() 
                if k in valid_fields and v is not None
            }
            
            # 3. Ensure vendor_id and vertical_id are set correctly
            filtered_data["vendor_id"] = vendor_id
            if "vertical_id" in data and data["vertical_id"]:
                filtered_data["vertical_id"] = str(data["vertical_id"])

            # 4. Handle date and string conversions (str expected in model)
            # Numeric fields like SKU might be read as int/float by pandas
            string_fields = ["sku", "mfd_date", "expiry_date", "manufacturer", "category"]
            for field in string_fields:
                if field in filtered_data:
                    val = filtered_data[field]
                    if isinstance(val, (datetime,)):
                        filtered_data[field] = val.strftime("%Y-%m-%d")
                    elif not isinstance(val, (str, bytes)) and val is not None:
                        # Convert numeric types to string (avoiding .0 for integers)
                        if isinstance(val, float) and val.is_integer():
                            filtered_data[field] = str(int(val))
                        else:
                            filtered_data[field] = str(val)
            
            # 5. Instantiate model
            it = StoreItem(**filtered_data)
            
            # 6. Save individually (Odmantic save)
            await engine.save(it)
            items.append(it)
            
        except Exception as e:
            # Log error for this specific row and continue
            print(f"DEBUG: Error creating store item row: {data.get('name', 'Unknown')}. Error: {e}")
            continue
            
    return items


async def bulk_delete_store_items(engine: AIOEngine, vendor_id: str, item_ids: List[str]) -> int:
    """
    Bulk delete store items for a specific vendor.
    """
    object_ids = [ObjectId(iid) for iid in item_ids]
    
    collection = engine.get_collection(StoreItem)
    result = await collection.delete_many({
        "_id": {"$in": object_ids},
        "vendor_id": vendor_id
    })
    
    return result.deleted_count

