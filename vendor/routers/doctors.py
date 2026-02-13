from fastapi import APIRouter, Depends, HTTPException
from odmantic import AIOEngine

from core.database import get_engine
from core.security import require_vendor
from utils.response import success_response

from vendor.schemas.doctor import DoctorCreateRequest
from vendor.services.doctor_service import create_doctor


router = APIRouter(
    prefix="/vendor/onboarding",
    tags=["Vendor Onboarding - Doctors"],
)


@router.post("/doctors")
async def add_doctor(
    payload: DoctorCreateRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token["vendor_id"]

    doctor = await create_doctor(engine, vendor_id, payload)

    return success_response(
        message="Doctor added",
        data={
            "doctor_id": str(doctor.id),
            "name": doctor.name,
            "specialization": doctor.specialization,
        },
    )
