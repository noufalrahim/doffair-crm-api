from fastapi import APIRouter, Depends, Query, File, UploadFile
from fastapi.responses import StreamingResponse
import pandas as pd
import io
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
    delete_medication,
    bulk_create_medications,
    count_medications
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

@router.get("/public-template")
async def get_medication_import_template():
    """
    Download a sample XLSX template for medication bulk import.
    """
    columns = [
        "medicine_id", "name", "brand_name", "generic_composition", 
        "description", "category", "dosage_form", "strength", 
        "manufacturer", "is_prescription_required", "indications", 
        "contraindications", "side_effects", "drug_interactions", 
        "storage_instructions", "schedule_class", "barcode", "qr_code", 
        "quantity_to_give", "stock_quantity", "unit", "base_price", 
        "purchase_price", "selling_price", "batch_id", "supplier_name", 
        "supplier_contact", "mfd_date", "expiry_date", "last_restocked_date", 
        "pack_size", "units_per_pack", "reorder_level", "reorder_quantity", 
        "location", "dosage", "frequency", "duration", "notes", "status"
    ]
    
    # Create an empty DataFrame with these columns
    df = pd.DataFrame(columns=columns)
    
    # Add a sample row
    sample_row = {
        "medicine_id": "SKU-PARA-001",
        "name": "Paracetamol 500mg",
        "brand_name": "Calpol",
        "generic_composition": "Paracetamol IP 500mg",
        "description": "Pain reliever and fever reducer",
        "category": "Analgesics",
        "dosage_form": "Tablet",
        "strength": "500 mg",
        "manufacturer": "HealthCorp",
        "is_prescription_required": False,
        "indications": "Fever, Headache",
        "contraindications": "Hypersensitivity",
        "side_effects": "Nausea",
        "drug_interactions": "Alcohol",
        "storage_instructions": "Store below 30°C",
        "schedule_class": "Schedule H",
        "barcode": "1234567890",
        "qr_code": "QR12345",
        "quantity_to_give": "1 tablet",
        "stock_quantity": 100,
        "unit": "TABLET",
        "base_price": 5.0,
        "purchase_price": 3.0,
        "selling_price": 5.0,
        "batch_id": "BATCH001",
        "supplier_name": "ABC Pharma",
        "supplier_contact": "9876543210",
        "mfd_date": "2024-01-01",
        "expiry_date": "2026-01-01",
        "last_restocked_date": "2024-03-01",
        "pack_size": "10 tablets per strip",
        "units_per_pack": 10,
        "reorder_level": 20,
        "reorder_quantity": 50,
        "location": "Shelf A1",
        "dosage": "500mg",
        "frequency": "Three times a day",
        "duration": "5 days",
        "notes": "Take after meals",
        "status": "Active"
    }
    df = pd.concat([df, pd.DataFrame([sample_row])], ignore_index=True)
    
    # Write to BytesIO
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Medications')
    output.seek(0)
    
    headers = {
        'Content-Disposition': 'attachment; filename="medication_import_template.xlsx"'
    }
    
    return StreamingResponse(
        output, 
        headers=headers, 
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
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
        **{**medication.model_dump(), "id": str(medication.id)}
    )
    
    return success_response(
        message="Medication created successfully",
        data=response_data.model_dump()
    ).model_dump()

@router.get("", response_model=APIResponse)
async def list_medications_endpoint(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by medication name (case-insensitive)"),
    vertical_id: Optional[str] = Query(None, description="Filter by vertical ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: Optional[int] = Query(None, ge=1, description="Number of items per page"),
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    List all medications for the vendor with pagination support.
    
    Optional **is_active** filter can be used to show only active/inactive medications.
    Optional **search** filter can be used to search medications by name.
    """
    vendor_id = current_vendor["vendor_id"]
    
    # Calculate skip for pagination
    skip = (page - 1) * limit if limit else 0
    
    medications = await list_medications(engine, vendor_id, vertical_id, is_active, search, skip, limit)
    total_count = await count_medications(engine, vendor_id, vertical_id, is_active, search)
    
    medication_responses = [
        MedicationResponse(
            **{**m.model_dump(), "id": str(m.id)}
        ).model_dump()
        for m in medications
    ]
    
    response_data = MedicationListResponse(
        total=total_count,
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
        **{**medication.model_dump(), "id": str(medication.id)}
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
        **{**medication.model_dump(), "id": str(medication.id)}
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

@router.post("/bulk-import", response_model=APIResponse)
async def bulk_import_medications_endpoint(
    file: UploadFile = File(...),
    vertical_id: str = Query(...),
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Bulk import medications from CSV or XLSX file.
    """
    vendor_id = current_vendor["vendor_id"]
    
    contents = await file.read()
    if file.filename.endswith('.csv'):
        df = pd.read_csv(io.BytesIO(contents))
    elif file.filename.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(io.BytesIO(contents))
    else:
        return error_response(message="Unsupported file format. Please upload CSV or XLSX.")
    
    # Replace NaN with None for Odmantic/MongoDB
    df = df.where(pd.notnull(df), None)
    
    medications_data = df.to_dict(orient='records')
    
    # Add vertical_id to each record if not present
    for item in medications_data:
        item['vertical_id'] = vertical_id
    
    try:
        medications = await bulk_create_medications(engine, vendor_id, medications_data)
        
        return success_response(
            message=f"Successfully processed import. {len(medications)} medications imported.",
            data={"imported_count": len(medications), "received_count": len(medications_data)}
        ).model_dump()
    except Exception as e:
        print(f"ERROR: Bulk import failed: {e}")
        return error_response(message=f"Bulk import failed: {str(e)}")
