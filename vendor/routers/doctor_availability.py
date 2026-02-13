from fastapi import APIRouter, Depends, HTTPException, Query
from odmantic import AIOEngine
import calendar
from datetime import datetime

from core.database import get_engine
from core.security import require_vendor
from utils.response import success_response

from vendor.schemas.doctor import DoctorAvailabilityRequest
from vendor.schemas.holiday import HolidayCreateRequest, HolidayResponse
from vendor.services.doctor_availability_service import (
    add_doctor_availability,
    get_vendor_availability,
)
from vendor.services.holiday_service import (
    add_holiday,
    get_vendor_holidays,
    delete_holiday,
)


router = APIRouter(
    prefix="/vendor/onboarding",
    tags=["Vendor Onboarding - Availability"],
)


@router.post("/availability")
async def add_availability(
    payload: list[DoctorAvailabilityRequest],
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token["vendor_id"]
    availabilities = await add_doctor_availability(engine, vendor_id, payload)

    return success_response(
        message="Availability added",
        data=[
            {
                "vendor_id": a.vendor_id,
                "vertical_id": a.vertical_id,
                "doctor_id": a.doctor_id,
                "day_of_week": a.day_of_week,
                "start_time": a.start_time,
                "end_time": a.end_time,
            }
            for a in availabilities
        ],
    )

@router.get("/availability")
async def list_availability(
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
    vertical_id: str = Query(None),
    doctor_id: str = Query(None),
    date: datetime = Query(None, description="Check availability for a specific date"),
):
    """
    Get vendor availability grouped by day. 
    If a specific date is provided, holidays and custom overrides are taken into account.
    """
    vendor_id = token["vendor_id"]
    availabilities = await get_vendor_availability(
        engine, vendor_id, vertical_id=vertical_id, doctor_id=doctor_id, specific_date=date
    )

    # Group by day
    grouped = {}
    for a in availabilities:
        day_idx = a.day_of_week
        if day_idx not in grouped:
            grouped[day_idx] = {
                "day_index": day_idx,
                "day_name": calendar.day_name[day_idx],
                "slots": [],
            }
        grouped[day_idx]["slots"].append({
            "start_time": a.start_time,
            "end_time": a.end_time,
        })

    # Convert to sorted list
    result = sorted(grouped.values(), key=lambda x: x["day_index"])

    return success_response(data=result)


# ============================================
# Holiday Management
# ============================================

@router.post("/holidays", response_model=HolidayResponse)
async def create_holiday(
    payload: HolidayCreateRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """Add a new holiday or custom availability override"""
    vendor_id = token["vendor_id"]
    holiday = await add_holiday(engine, vendor_id, payload.model_dump())
    
    return success_response(
        message="Holiday added",
        data=HolidayResponse(
            id=str(holiday.id),
            vertical_id=holiday.vertical_id,
            doctor_id=holiday.doctor_id,
            date=holiday.date,
            name=holiday.name,
            is_all_day=holiday.is_all_day,
            slots=[{"start_time": s.start_time, "end_time": s.end_time} for s in holiday.slots],
            created_at=holiday.created_at
        ).model_dump()
    )


@router.get("/holidays")
async def list_holidays(
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
    start_date: datetime = Query(None),
    end_date: datetime = Query(None),
):
    """List all custom holidays for the vendor"""
    vendor_id = token["vendor_id"]
    holidays = await get_vendor_holidays(engine, vendor_id, start_date, end_date)
    
    return success_response(
        data=[
            HolidayResponse(
                id=str(h.id),
                vertical_id=h.vertical_id,
                doctor_id=h.doctor_id,
                date=h.date,
                name=h.name,
                is_all_day=h.is_all_day,
                slots=[{"start_time": s.start_time, "end_time": s.end_time} for s in h.slots],
                created_at=h.created_at
            ).model_dump()
            for h in holidays
        ]
    )


@router.delete("/holidays/{holiday_id}")
async def remove_holiday(
    holiday_id: str,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """Delete a holiday override"""
    vendor_id = token["vendor_id"]
    success = await delete_holiday(engine, holiday_id, vendor_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Holiday not found or unauthorized")
        
    return success_response(message="Holiday removed")
