from odmantic import AIOEngine
from datetime import datetime
from vendor.models.doctor_availability import Availability
from vendor.models.holiday import Holiday


async def add_doctor_availability(
    engine: AIOEngine,
    vendor_id: str,
    payload: list,
):
    import asyncio

    availabilities = [
        Availability(
            vendor_id=vendor_id,
            vertical_id=p.vertical_id,
            location_id=getattr(p, "location_id", None),
            care_professional_id=getattr(p, "care_professional_id", None) or getattr(p, "doctor_id", None),
            doctor_id=getattr(p, "doctor_id", None),
            day_of_week=p.day_of_week,
            start_time=p.start_time,
            end_time=p.end_time,
        )
        for p in payload
    ]

    # Delete existing availability for these professionals under this vendor
    # Extract IDs to clear existing availability
    ids_to_clear = list(set(
        getattr(p, "care_professional_id", None) or getattr(p, "doctor_id", None) 
        for p in payload 
        if getattr(p, "care_professional_id", None) or getattr(p, "doctor_id", None)
    ))
    
    if ids_to_clear:
        await engine.remove(
            Availability,
            (Availability.vendor_id == vendor_id) & 
            ((Availability.care_professional_id.in_(ids_to_clear)) | (Availability.doctor_id.in_(ids_to_clear)))
        )
    else:
        # Fallback to legacy behavior if no specific IDs are provided (clear all for vendor - risky but matches legacy)
        await engine.remove(Availability, Availability.vendor_id == vendor_id)

    await asyncio.gather(*[engine.save(a) for a in availabilities])
    return availabilities


async def get_vendor_availability(
    engine: AIOEngine,
    vendor_id: str,
    vertical_id: str = None,
    doctor_id: str = None,
    care_professional_id: str = None,
    location_id: str = None,
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
        
        holidays_cursor = engine.get_collection(Holiday).find(holiday_query)
        holidays = await holidays_cursor.to_list(length=10)
        
        target_id = care_professional_id or doctor_id
        
        relevant_holiday = None
        if target_id:
            relevant_holiday = next((h for h in holidays if h.get("doctor_id") == target_id or h.get("care_professional_id") == target_id), None)
        
        if not relevant_holiday and vertical_id:
            relevant_holiday = next((h for h in holidays if h.get("vertical_id") == vertical_id), None)
            
        if not relevant_holiday:
            relevant_holiday = next((h for h in holidays if not h.get("doctor_id") and not h.get("care_professional_id") and not h.get("vertical_id")), None)
            
        if relevant_holiday:
            if relevant_holiday.get("is_all_day"):
                return [] # No availability
            else:
                # Return custom hours as availability
                slots = []
                for s in relevant_holiday.get("slots", []):
                    slots.append(Availability(
                        vendor_id=vendor_id,
                        vertical_id=vertical_id or "HOLIDAY",
                        day_of_week=specific_date.weekday(),
                        start_time=s.get("start_time"),
                        end_time=s.get("end_time")
                    ))
                return slots

    # 2. Proceed with regular weekly availability
    filters = [Availability.vendor_id == vendor_id]
    
    if vertical_id:
        if ObjectId.is_valid(vertical_id):
            filters.append((Availability.vertical_id == vertical_id) | (Availability.vertical_id == ObjectId(vertical_id)))
        else:
            filters.append(Availability.vertical_id == vertical_id)
    
    target_id = care_professional_id or doctor_id
    if target_id:
        if ObjectId.is_valid(target_id):
            filters.append(
                (Availability.care_professional_id == target_id) | 
                (Availability.care_professional_id == ObjectId(target_id)) |
                (Availability.doctor_id == target_id) |
                (Availability.doctor_id == ObjectId(target_id))
            )
        else:
            filters.append(
                (Availability.care_professional_id == target_id) | 
                (Availability.doctor_id == target_id)
            )

    if location_id:
        filters.append(Availability.location_id == location_id)

    results = await engine.find(Availability, *filters, sort=Availability.day_of_week.asc())
    return results
