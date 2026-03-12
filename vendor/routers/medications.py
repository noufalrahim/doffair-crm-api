from fastapi import APIRouter, Depends, Query
from odmantic import AIOEngine
from typing import Optional

from core.database import get_engine
from core.security import get_current_vendor
from utils.response import success_response, error_response
from vendor.services.medication_service import (
    create_medication,
    get_medication_by_id,
    list_medications,
    update_medication,
    delete_medication
)
from schemas.common import APIResponse
from vendor.schemas.medication import (
    MedicationCreate,
    MedicationUpdate,
    MedicationResponse,
    MedicationListResponse
)

router = APIRouter(
    prefix="/vendor/medications",
    tags=["Vendor - Medications"]
)

@router.post("", response_model=APIResponse)
async def create_medication_endpoint(
    data: MedicationCreate,
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Create a new medication record in the master list.
    
    Returns the created medication details.
    """
    vendor_id = current_vendor["vendor_id"]
    medication = await create_medication(engine, vendor_id, data)
    
    response_data = MedicationResponse(
        id=str(medication.id),
        vendor_id=medication.vendor_id,
        name=medication.name,
        dosage=medication.dosage,
        frequency=medication.frequency,
        duration=medication.duration,
        notes=medication.notes,
        is_active=medication.is_active,
        created_at=medication.created_at,
        updated_at=medication.updated_at
    )
    
    return success_response(
        message="Medication created successfully",
        data=response_data.model_dump()
    ).model_dump()

@router.get("", response_model=APIResponse)
async def list_medications_endpoint(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by medication name (case-insensitive)"),
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    List all medications for the vendor.
    
    Optional **is_active** filter can be used to show only active/inactive medications.
    Optional **search** filter can be used to search medications by name.
    """
    vendor_id = current_vendor["vendor_id"]
    medications = await list_medications(engine, vendor_id, is_active, search)
    
    medication_responses = [
        MedicationResponse(
            id=str(m.id),
            vendor_id=m.vendor_id,
            name=m.name,
            dosage=m.dosage,
            frequency=m.frequency,
            duration=m.duration,
            notes=m.notes,
            is_active=m.is_active,
            created_at=m.created_at,
            updated_at=m.updated_at
        ).model_dump()
        for m in medications
    ]
    
    response_data = MedicationListResponse(
        total=len(medication_responses),
        medications=medication_responses
    )
    
    return success_response(
        message="Medications retrieved successfully",
        data=response_data.model_dump()
    ).model_dump()

@router.get("/{medication_id}", response_model=APIResponse)
async def get_medication_endpoint(
    medication_id: str,
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Get detailed information about a specific medication.
    """
    vendor_id = current_vendor["vendor_id"]
    medication = await get_medication_by_id(engine, vendor_id, medication_id)
    
    response_data = MedicationResponse(
        id=str(medication.id),
        vendor_id=medication.vendor_id,
        name=medication.name,
        dosage=medication.dosage,
        frequency=medication.frequency,
        duration=medication.duration,
        notes=medication.notes,
        is_active=medication.is_active,
        created_at=medication.created_at,
        updated_at=medication.updated_at
    )
    
    return success_response(
        message="Medication retrieved successfully",
        data=response_data.model_dump()
    ).model_dump()

@router.patch("/{medication_id}", response_model=APIResponse)
async def update_medication_endpoint(
    medication_id: str,
    data: MedicationUpdate,
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Update an existing medication record.
    """
    vendor_id = current_vendor["vendor_id"]
    medication = await update_medication(engine, vendor_id, medication_id, data)
    
    response_data = MedicationResponse(
        id=str(medication.id),
        vendor_id=medication.vendor_id,
        name=medication.name,
        dosage=medication.dosage,
        frequency=medication.frequency,
        duration=medication.duration,
        notes=medication.notes,
        is_active=medication.is_active,
        created_at=medication.created_at,
        updated_at=medication.updated_at
    )
    
    return success_response(
        message="Medication updated successfully",
        data=response_data.model_dump()
    ).model_dump()

@router.delete("/{medication_id}", response_model=APIResponse)
async def delete_medication_endpoint(
    medication_id: str,
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Soft delete a medication (marks as inactive).
    """
    vendor_id = current_vendor["vendor_id"]
    await delete_medication(engine, vendor_id, medication_id)
    
    return success_response(
        message="Medication deleted successfully",
        data={"medication_id": medication_id, "deleted": True}
    ).model_dump()
