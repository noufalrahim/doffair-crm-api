from fastapi import APIRouter, Depends, Query
from odmantic import AIOEngine
from typing import Optional, List

from core.database import get_engine
from core.security import get_current_vendor
from utils.response import success_response, error_response
from schemas.common import APIResponse
from vendor.services.prescription_data_service import (
    create_prescription_data,
    get_prescription_data_by_id,
    list_prescriptions_data,
    update_prescription_data,
    delete_prescription_data
)
from vendor.schemas.prescription_data import (
    PrescriptionDataCreate,
    PrescriptionDataUpdate,
    PrescriptionDataResponse,
    PrescriptionDataListResponse,
    PrescriptionMedicationSchema
)

router = APIRouter(
    prefix="/vendor/prescriptions-data",
    tags=["Vendor - Prescriptions Data"]
)

@router.post("", response_model=APIResponse)
@router.post("/create", response_model=APIResponse)
async def create_prescription_endpoint(
    data: PrescriptionDataCreate,
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Create a structured prescription.
    
    If **booking_id** is provided, details like **pet_name**, **owner_name**, and **owner_id** 
    will be automatically fetched from the booking if not provided in the request.
    
    Returns the created prescription record.
    """
    vendor_id = current_vendor["vendor_id"]
    prescription = await create_prescription_data(engine, vendor_id, data)
    
    response_data = PrescriptionDataResponse(
        id=str(prescription.id),
        vendor_id=prescription.vendor_id,
        booking_id=prescription.booking_id,
        pet_name=prescription.pet_name,
        pet_id=prescription.pet_id,
        owner_name=prescription.owner_name,
        owner_id=prescription.owner_id,
        diagnosis=prescription.diagnosis,
        medications=[PrescriptionMedicationSchema(**m.model_dump()) for m in prescription.medications],
        instructions=prescription.instructions,
        follow_up_date=prescription.follow_up_date,
        is_active=prescription.is_active,
        created_at=prescription.created_at,
        updated_at=prescription.updated_at
    )
    
    return success_response(
        message="Prescription created successfully",
        data=response_data.model_dump()
    ).model_dump()

@router.get("", response_model=APIResponse)
async def list_prescriptions_endpoint(
    booking_id: Optional[str] = Query(None, description="Filter by booking ID"),
    pet_id: Optional[str] = Query(None, description="Filter by pet ID"),
    owner_id: Optional[str] = Query(None, description="Filter by owner ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    List structured prescriptions for the vendor.
    
    Allows filtering by **booking_id**, **pet_id**, or **owner_id**.
    """
    vendor_id = current_vendor["vendor_id"]
    prescriptions = await list_prescriptions_data(engine, vendor_id, booking_id, pet_id, owner_id, is_active)
    
    prescription_responses = [
        PrescriptionDataResponse(
            id=str(p.id),
            vendor_id=p.vendor_id,
            booking_id=p.booking_id,
            pet_name=p.pet_name,
            pet_id=p.pet_id,
            owner_name=p.owner_name,
            owner_id=p.owner_id,
            diagnosis=p.diagnosis,
            medications=[PrescriptionMedicationSchema(**m.model_dump()) for m in p.medications],
            instructions=p.instructions,
            follow_up_date=p.follow_up_date,
            is_active=p.is_active,
            created_at=p.created_at,
            updated_at=p.updated_at
        ).model_dump()
        for p in prescriptions
    ]
    
    response_data = PrescriptionDataListResponse(
        total=len(prescription_responses),
        prescriptions=prescription_responses
    )
    
    return success_response(
        message="Prescriptions retrieved successfully",
        data=response_data.model_dump()
    ).model_dump()

@router.get("/{prescription_id}", response_model=APIResponse)
async def get_prescription_endpoint(
    prescription_id: str,
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Get detailed information about a specific structured prescription.
    """
    vendor_id = current_vendor["vendor_id"]
    p = await get_prescription_data_by_id(engine, vendor_id, prescription_id)
    
    response_data = PrescriptionDataResponse(
        id=str(p.id),
        vendor_id=p.vendor_id,
        booking_id=p.booking_id,
        pet_name=p.pet_name,
        pet_id=p.pet_id,
        owner_name=p.owner_name,
        owner_id=p.owner_id,
        diagnosis=p.diagnosis,
        medications=[PrescriptionMedicationSchema(**m.model_dump()) for m in p.medications],
        instructions=p.instructions,
        follow_up_date=p.follow_up_date,
        is_active=p.is_active,
        created_at=p.created_at,
        updated_at=p.updated_at
    )
    
    return success_response(
        message="Prescription retrieved successfully",
        data=response_data.model_dump()
    ).model_dump()

@router.patch("/{prescription_id}", response_model=APIResponse)
async def update_prescription_endpoint(
    prescription_id: str,
    data: PrescriptionDataUpdate,
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Update an existing structured prescription.
    """
    vendor_id = current_vendor["vendor_id"]
    p = await update_prescription_data(engine, vendor_id, prescription_id, data)
    
    response_data = PrescriptionDataResponse(
        id=str(p.id),
        vendor_id=p.vendor_id,
        booking_id=p.booking_id,
        pet_name=p.pet_name,
        pet_id=p.pet_id,
        owner_name=p.owner_name,
        owner_id=p.owner_id,
        diagnosis=p.diagnosis,
        medications=[PrescriptionMedicationSchema(**m.model_dump()) for m in p.medications],
        instructions=p.instructions,
        follow_up_date=p.follow_up_date,
        is_active=p.is_active,
        created_at=p.created_at,
        updated_at=p.updated_at
    )
    
    return success_response(
        message="Prescription updated successfully",
        data=response_data.model_dump()
    ).model_dump()

@router.delete("/{prescription_id}", response_model=APIResponse)
async def delete_prescription_endpoint(
    prescription_id: str,
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Soft delete a prescription (marks as inactive).
    """
    vendor_id = current_vendor["vendor_id"]
    await delete_prescription_data(engine, vendor_id, prescription_id)
    
    return success_response(
        message="Prescription deleted successfully",
        data={"prescription_id": prescription_id, "deleted": True}
    ).model_dump()
