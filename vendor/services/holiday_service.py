from odmantic import AIOEngine
from vendor.models.holiday import Holiday, HolidaySlot
from typing import List, Optional
from datetime import datetime

async def add_holiday(
    engine: AIOEngine,
    vendor_id: str,
    payload: dict,
):
    holiday = Holiday(
        vendor_id=vendor_id,
        vertical_id=payload.get("vertical_id"),
        date=payload.get("date"),
        name=payload.get("name"),
        is_all_day=payload.get("is_all_day", True),
        slots=[
            HolidaySlot(start_time=s.get("start_time"), end_time=s.get("end_time"))
            for s in payload.get("slots", [])
        ]
    )
    await engine.save(holiday)
    return holiday

async def get_vendor_holidays(
    engine: AIOEngine,
    vendor_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    query = {"vendor_id": vendor_id}
    
    if start_date or end_date:
        date_query = {}
        if start_date:
            date_query["$gte"] = start_date
        if end_date:
            date_query["$lte"] = end_date
        query["date"] = date_query
        
    cursor = engine.get_collection(Holiday).find(query).sort("date", 1)
    raw_results = await cursor.to_list(length=100)
    
    results = []
    for r in raw_results:
        # Convert slots from dict to HolidaySlot objects for attribute access
        if "slots" in r and isinstance(r["slots"], list):
            r["slots"] = [
                HolidaySlot(start_time=s.get("start_time"), end_time=s.get("end_time"))
                for s in r["slots"]
            ]
        
        r["id"] = r.pop("_id")
        results.append(Holiday.model_construct(**r))
        
    return results

async def delete_holiday(
    engine: AIOEngine,
    holiday_id: str,
    vendor_id: str,
):
    from bson import ObjectId
    if not ObjectId.is_valid(holiday_id):
        return False
        
    result = await engine.get_collection(Holiday).delete_one({
        "_id": ObjectId(holiday_id),
        "vendor_id": vendor_id
    })
    return result.deleted_count > 0
