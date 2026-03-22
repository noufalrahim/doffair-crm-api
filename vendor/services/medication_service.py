from odmantic import AIOEngine
from bson import ObjectId
from datetime import datetime
from fastapi import HTTPException
from typing import List, Optional

from vendor.models.medication import Medication
from vendor.schemas.medication import MedicationCreate, MedicationUpdate

async def create_medication(engine: AIOEngine, vendor_id: Optional[str], data: MedicationCreate) -> Medication:
    medication = Medication(
        vendor_id=vendor_id,
        **data.model_dump(exclude={"vendor_id"})
    )
    if data.vendor_id:
        medication.vendor_id = data.vendor_id
        
    await engine.save(medication)
    return medication

async def get_medication_by_id(engine: AIOEngine, vendor_id: Optional[str], medication_id: str) -> Medication:
    query = [Medication.id == ObjectId(medication_id)]
    if vendor_id:
        query.append(Medication.vendor_id == vendor_id)
        
    medication = await engine.find_one(Medication, *query)
    if not medication:
        raise HTTPException(status_code=404, detail="Medication not found")
    return medication

async def list_medications(
    engine: AIOEngine, 
    vendor_id: Optional[str] = None, 
    vertical_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None
) -> List[Medication]:
    query = []
    if vendor_id:
        query.append(Medication.vendor_id == vendor_id)
    if vertical_id:
        query.append(Medication.vertical_id == vertical_id)
        
    if is_active is not None:
        query.append(Medication.is_active == is_active)
    
    if search:
        query.append(Medication.name.match(f"(?i).*{search}.*"))
    
    medications = await engine.find(Medication, *query)
    return medications

async def update_medication(engine: AIOEngine, vendor_id: str, medication_id: str, data: MedicationUpdate) -> Medication:
    medication = await get_medication_by_id(engine, vendor_id, medication_id)
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(medication, key, value)
    
    medication.updated_at = datetime.utcnow()
    await engine.save(medication)
    return medication

async def delete_medication(engine: AIOEngine, vendor_id: str, medication_id: str) -> bool:
    medication = await get_medication_by_id(engine, vendor_id, medication_id)
    # Hard delete
    await engine.delete(medication)
    return True

async def bulk_create_medications(engine: AIOEngine, vendor_id: str, medications_data: List[dict]) -> List[Medication]:
    """
    Bulk create medications with robustness for varied input data.
    Filters out invalid fields and skips empty/incomplete rows.
    """
    medications = []
    
    # Identify valid model fields to prevent TypeError from unknown keys
    valid_fields = set(Medication.model_fields.keys())
    
    for data in medications_data:
        try:
            # 1. Skip rows missing critical info (e.g., name)
            if not data.get("name"):
                print("DEBUG: Skipping medication row with missing name")
                continue
                
            # 2. Filter data to only include valid model fields
            filtered_data = {
                k: v for k, v in data.items() 
                if k in valid_fields and v is not None
            }
            
            # 3. Ensure vendor_id is set
            filtered_data["vendor_id"] = vendor_id
            
            # 4. Instantiate model
            m = Medication(**filtered_data)
            
            # 5. Save individually (Odmantic save)
            await engine.save(m)
            medications.append(m)
            
        except Exception as e:
            # Log error for this specific row and continue
            print(f"DEBUG: Error creating medication row: {data.get('name', 'Unknown')}. Error: {e}")
            continue
            
    return medications
