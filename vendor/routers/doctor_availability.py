from fastapi import APIRouter, Depends, HTTPException
from odmantic import AIOEngine

from core.database import get_engine
from core.security import require_vendor
from utils.response import success_response

from vendor.schemas.doctor import DoctorAvailabilityRequest
from vendor.services.doctor_availability_service import add_doctor_availability


router = APIRouter(
    prefix="/vendor/onboarding",
    tags=["Vendor Onboarding - Availability"],
)


@router.post("/{vendor_id}/availability")
async def add_availability(
    vendor_id: str,
    payload: list[DoctorAvailabilityRequest],
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    if token["vendor_id"] != vendor_id:
        raise HTTPException(status_code=403, detail="Access denied")

    availabilities = await add_doctor_availability(engine, payload)

    return success_response(
        message="Availability added",
        data=[
            {
                "service_type_id": a.service_type_id,
                "doctor_id": a.doctor_id,
                "day_of_week": a.day_of_week,
                "start_time": a.start_time,
                "end_time": a.end_time,
            }
            for a in availabilities
        ],
    )
