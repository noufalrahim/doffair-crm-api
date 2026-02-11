from odmantic import AIOEngine
from datetime import datetime
from vendor.models.doctor_availability import DoctorAvailability
from vendor.models.holiday import Holiday


async def add_doctor_availability(
    engine: AIOEngine,
    vendor_id: str,
    payload: list,
):
    import asyncio

    availabilities = [
        DoctorAvailability(
            vendor_id=vendor_id,
            service_type_id=p.service_type_id,
            doctor_id=p.doctor_id,
            day_of_week=p.day_of_week,
            start_time=p.start_time,
            end_time=p.end_time,
        )
        for p in payload
    ]

    await asyncio.gather(*[engine.save(a) for a in availabilities])
    return availabilities


async def get_vendor_availability(
    engine: AIOEngine,
    vendor_id: str,
    service_type_id: str = None,
    doctor_id: str = None,
    specific_date: datetime = None,
):
    """Fetch all availability records for a vendor with optional filters and holiday overrides"""
    from bson import ObjectId
    
    # 1. Check for holidays if a specific date is provided
    if specific_date:
        holiday_query = {
            "vendor_id": vendor_id,
            "date": {
                "$gte": specific_date.replace(hour=0, minute=0, second=0, microsecond=0),
                "$lte": specific_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            }
        }
        
        # Priority: Doctor-specific holiday -> Service-specific holiday -> Vendor-wide holiday
        # But for now, we'll just find the most relevant one.
        holidays_cursor = engine.get_collection(Holiday).find(holiday_query)
        holidays = await holidays_cursor.to_list(length=10)
        
        # Filtering logic for specific holiday
        relevant_holiday = None
        if doctor_id:
            relevant_holiday = next((h for h in holidays if h.get("doctor_id") == doctor_id), None)
        
        if not relevant_holiday and service_type_id:
            relevant_holiday = next((h for h in holidays if h.get("service_type_id") == service_type_id), None)
            
        if not relevant_holiday:
            relevant_holiday = next((h for h in holidays if not h.get("doctor_id") and not h.get("service_type_id")), None)
            
        if relevant_holiday:
            if relevant_holiday.get("is_all_day"):
                return [] # No availability
            else:
                # Return custom hours as availability
                slots = []
                for s in relevant_holiday.get("slots", []):
                    slots.append(DoctorAvailability(
                        vendor_id=vendor_id,
                        service_type_id=service_type_id or "HOLIDAY",
                        day_of_week=specific_date.weekday(),
                        start_time=s.get("start_time"),
                        end_time=s.get("end_time")
                    ))
                return slots

    # 2. Proceed with regular weekly availability if no holiday override
    # Create a flexible query for vendor_id (allow missing for legacy data)
    query = {
        "$or": [
            {"vendor_id": vendor_id},
            {"vendor_id": {"$exists": False}}
        ]
    }
    
    if service_type_id:
        # Try both string and ObjectId for service_type_id
        if ObjectId.is_valid(service_type_id):
            query["service_type_id"] = {"$in": [service_type_id, ObjectId(service_type_id)]}
        else:
            query["service_type_id"] = service_type_id
    
    # If doctor_id is provided, filter by it (trying both str and ObjectId)
    if doctor_id:
        if ObjectId.is_valid(doctor_id):
            query["doctor_id"] = {"$in": [doctor_id, ObjectId(doctor_id)]}
        else:
            query["doctor_id"] = doctor_id
    # Note: If no doctor_id provided, we return everything for that service type

    # Try the new collection first (linked to model config 'availability')
    cursor = engine.get_collection(DoctorAvailability).find(query).sort("day_of_week", 1)
    raw_results = await cursor.to_list(length=100)
    
    # Fallback to legacy collection if new one is empty
    if not raw_results:
        # engine.get_collection(DoctorAvailability) uses the name in model_config
        # We manually access the legacy name via motor-style access if available
        # or just try to find if we can use a different name.
        # Since we can't easily change the model's collection name at runtime, 
        # let's try to query the legacy collection name directly if the engine allows it.
        try:
            legacy_cursor = engine.database["doctor_availability"].find(query).sort("day_of_week", 1)
            raw_results = await legacy_cursor.to_list(length=100)
        except Exception:
            pass

    # Convert to objects
    results = []
    for r in raw_results:
        r["id"] = r.pop("_id")
        # Use model_construct to bypass validation if schema slightly differs
        results.append(DoctorAvailability.model_construct(**r))

    return results
