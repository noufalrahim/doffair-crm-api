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


@router.post("/{vendor_id}/doctors")
async def add_doctor(
    vendor_id: str,
    payload: DoctorCreateRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    if token["vendor_id"] != vendor_id:
        raise HTTPException(status_code=403, detail="Access denied")

    doctor = await create_doctor(engine, vendor_id, payload)

    return success_response(
        message="Doctor added",
        data={
            "doctor_id": str(doctor.id),
            "name": doctor.name,
            "specialization": doctor.specialization,
        },
    )
