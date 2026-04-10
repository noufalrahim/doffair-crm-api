from odmantic import AIOEngine
from bson import ObjectId
from datetime import datetime
from fastapi import HTTPException
from typing import List, Optional

from vendor.models.prescription_data import PrescriptionData, PrescriptionMedication
from vendor.schemas.prescription_data import PrescriptionDataCreate, PrescriptionDataUpdate

from user.models.booking import Booking

async def create_prescription_data(engine: AIOEngine, vendor_id: str, data: PrescriptionDataCreate) -> PrescriptionData:
    # Convert medications from schema to model
    medications = [
        PrescriptionMedication(**m.model_dump())
        for m in data.medications
    ]
    
    # 1. Fetch booking details to populate missing fields if booking_id is provided
    pet_name = data.pet_name
    pet_id = data.pet_id
    owner_name = data.owner_name
    owner_id = data.owner_id
    
    if data.booking_id:
        try:
            booking = await engine.find_one(Booking, Booking.id == ObjectId(data.booking_id))
            if booking:
                # Prioritize provided values, fallback to booking data
                if not pet_name: pet_name = booking.pet_name or ""
                # Booking model does not have pet_id, so we keep it as provided or empty
                if not owner_name: owner_name = booking.user_name
                if not owner_id: owner_id = booking.user_id
        except Exception:
            # If booking lookup fails (e.g. invalid ID), we continue with provided data
            pass
    
    prescription = PrescriptionData(
        vendor_id=vendor_id,
        booking_id=data.booking_id,
        pet_name=pet_name,
        pet_id=pet_id,
        owner_name=owner_name,
        owner_id=owner_id,
        complaints=data.complaints or "",
        medical_history=data.medical_history or "",
        drug_allergies=data.drug_allergies or "",
        tests_prescribed=data.tests_prescribed or "",
        diagnosis=data.diagnosis,
        medications=medications,
        instructions=data.instructions,
        follow_up_date=data.follow_up_date,
        clinic_name=data.clinic_name or "",
        doctor_name=data.doctor_name or "",
    )
    
    # Debug: Log what we're about to save
    print(f"DEBUG: Saving prescription with new fields:")
    print(f"  complaints: '{data.complaints}'")
    print(f"  medical_history: '{data.medical_history}'")
    print(f"  drug_allergies: '{data.drug_allergies}'")
    print(f"  tests_prescribed: '{data.tests_prescribed}'")
    print(f"  clinic_name: '{data.clinic_name}'")
    print(f"  doctor_name: '{data.doctor_name}'")
    
    await engine.save(prescription)
    
    # Debug: Log what was saved
    print(f"DEBUG: Saved prescription ID: {prescription.id}")
    print(f"  saved.complaints: '{prescription.complaints}'")
    print(f"  saved.medical_history: '{prescription.medical_history}'")
    print(f"  saved.drug_allergies: '{prescription.drug_allergies}'")
    print(f"  saved.tests_prescribed: '{prescription.tests_prescribed}'")
    print(f"  saved.clinic_name: '{prescription.clinic_name}'")
    print(f"  saved.doctor_name: '{prescription.doctor_name}'")
    
    return prescription

async def get_prescription_data_by_id(engine: AIOEngine, vendor_id: str, prescription_id: str) -> PrescriptionData:
    prescription = await engine.find_one(
        PrescriptionData, 
        PrescriptionData.id == ObjectId(prescription_id), 
        PrescriptionData.vendor_id == vendor_id
    )
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return prescription

async def list_prescriptions_data(
    engine: AIOEngine, 
    vendor_id: str, 
    booking_id: Optional[str] = None,
    pet_id: Optional[str] = None,
    owner_id: Optional[str] = None,
    is_active: Optional[bool] = None
) -> List[PrescriptionData]:
    query = [PrescriptionData.vendor_id == vendor_id]
    
    if booking_id:
        query.append(PrescriptionData.booking_id == booking_id)
    if pet_id:
        query.append(PrescriptionData.pet_id == pet_id)
    if owner_id:
        query.append(PrescriptionData.owner_id == owner_id)
    if is_active is not None:
        query.append(PrescriptionData.is_active == is_active)
    
    prescriptions = await engine.find(PrescriptionData, *query)
    return prescriptions

async def update_prescription_data(
    engine: AIOEngine, 
    vendor_id: str, 
    prescription_id: str, 
    data: PrescriptionDataUpdate
) -> PrescriptionData:
    prescription = await get_prescription_data_by_id(engine, vendor_id, prescription_id)
    
    update_data = data.model_dump(exclude_unset=True)
    
    # Handle medications special case
    if "medications" in update_data:
        prescription.medications = [
            PrescriptionMedication(**m)
            for m in update_data.pop("medications")
        ]
    
    for key, value in update_data.items():
        setattr(prescription, key, value)
    
    prescription.updated_at = datetime.utcnow()
    await engine.save(prescription)
    return prescription

async def delete_prescription_data(engine: AIOEngine, vendor_id: str, prescription_id: str) -> bool:
    prescription = await get_prescription_data_by_id(engine, vendor_id, prescription_id)
    # Soft delete
    prescription.is_active = False
    prescription.updated_at = datetime.utcnow()
    await engine.save(prescription)
    return True
