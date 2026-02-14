from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from odmantic import AIOEngine
import calendar

from core.database import get_engine
from core.security import require_vendor
from utils.response import success_response

from vendor.schemas.care_professional_availability import (
    CareProfessionalAvailabilityRequest,
    CareProfessionalAvailabilityResponse,
)
from vendor.services.doctor_availability_service import (
    add_doctor_availability,
    get_vendor_availability,
)


router = APIRouter(
    prefix="/vendor/care-professionals/availability",
    tags=["Vendor - Care Professional Availability"],
)


@router.post("")
async def set_availability(
    payload: List[CareProfessionalAvailabilityRequest],
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """Set availability for care professionals (bulk replace)"""
    vendor_id = token["vendor_id"]
    availabilities = await add_doctor_availability(engine, vendor_id, payload)

    return success_response(
        message="Availability updated",
        data=[
            {
                "id": str(a.id),
                "vendor_id": a.vendor_id,
                "vertical_id": a.vertical_id,
                "location_id": a.location_id,
                "care_professional_id": a.care_professional_id,
                "day_of_week": a.day_of_week,
                "start_time": a.start_time,
                "end_time": a.end_time,
            }
            for a in availabilities
        ],
    )


@router.get("")
async def list_availability(
    care_professional_id: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    vertical_id: Optional[str] = Query(None),
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """Get availability for care professionals"""
    vendor_id = token["vendor_id"]
    availabilities = await get_vendor_availability(
        engine, 
        vendor_id, 
        care_professional_id=care_professional_id,
        location_id=location_id,
        vertical_id=vertical_id
    )

    if care_professional_id:
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
                "id": str(a.id),
                "start_time": a.start_time,
                "end_time": a.end_time,
            })
        result = sorted(grouped.values(), key=lambda x: x["day_index"])
        return success_response(data=result)

    return success_response(
        data=[
            {
                "id": str(a.id),
                "vendor_id": a.vendor_id,
                "vertical_id": a.vertical_id,
                "location_id": a.location_id,
                "care_professional_id": a.care_professional_id,
                "day_of_week": a.day_of_week,
                "start_time": a.start_time,
                "end_time": a.end_time,
            }
            for a in availabilities
        ]
    )
