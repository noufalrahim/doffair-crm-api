from odmantic import AIOEngine
from bson import ObjectId
from datetime import datetime, timezone
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
    search: Optional[str] = None,
    skip: int = 0,
    limit: Optional[int] = None
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
    
    medications = await engine.find(Medication, *query, skip=skip, limit=limit, sort=Medication.created_at.desc())
    return medications

async def count_medications(
    engine: AIOEngine,
    vendor_id: Optional[str] = None,
    vertical_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None
) -> int:
    query = []
    if vendor_id:
        query.append(Medication.vendor_id == vendor_id)
    if vertical_id:
        query.append(Medication.vertical_id == vertical_id)
        
    if is_active is not None:
        query.append(Medication.is_active == is_active)
    
    if search:
        query.append(Medication.name.match(f"(?i).*{search}.*"))
        
    count = await engine.count(Medication, *query)
    return count

async def update_medication(engine: AIOEngine, vendor_id: str, medication_id: str, data: MedicationUpdate) -> Medication:
    print(f"DEBUG: Updating medication {medication_id} for vendor {vendor_id}")
    medication = await get_medication_by_id(engine, vendor_id, medication_id)
    
    update_data = data.model_dump(exclude_unset=True)
    print(f"DEBUG: Initial update data: {update_data}")
    
    # Identify valid model fields to prevent TypeError from unknown keys
    valid_fields = set(Medication.model_fields.keys())
    
    # Handle date and string conversions (str expected in model)
    string_fields = ["barcode", "qr_code", "supplier_contact", "medicine_id", "batch_id", "mfd_date", "expiry_date", "last_restocked_date"]
    
    for key, value in list(update_data.items()):
        if key not in valid_fields:
            print(f"DEBUG: Skipping invalid field for medication update: {key}")
            del update_data[key]
            continue
            
        if value is None:
            continue
            
        # Robust string conversion for numeric-looking fields
        if key in string_fields:
            if isinstance(value, (datetime,)):
                update_data[key] = value.strftime("%Y-%m-%d")
            elif not isinstance(value, str):
                if isinstance(value, float) and value.is_integer():
                    update_data[key] = str(int(value))
                else:
                    update_data[key] = str(value)
            print(f"DEBUG: Field {key} converted to {update_data[key]}")

    for key, value in update_data.items():
        setattr(medication, key, value)
    
    medication.updated_at = datetime.now(timezone.utc)
    await engine.save(medication)
    print(f"DEBUG: Medication {medication_id} updated successfully with keys: {list(update_data.keys())}")
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
    
    for i, data in enumerate(medications_data):
        try:
            # 1. Skip rows missing critical info (e.g., name)
            if not data.get("name"):
                print(f"DEBUG: Skipping medication row {i+1} with missing name")
                continue
                
            # 2. Filter data to only include valid model fields
            filtered_data = {
                k: v for k, v in data.items() 
                if k in valid_fields and v is not None
            }
            
            # 3. Ensure vendor_id and vertical_id are set correctly
            filtered_data["vendor_id"] = vendor_id
            if "vertical_id" in data and data["vertical_id"]:
                filtered_data["vertical_id"] = str(data["vertical_id"])

            # 4. Handle Boolean fields
            bool_fields = ["is_prescription_required", "near_expiry_flag", "is_expired", "is_active"]
            for field in bool_fields:
                if field in filtered_data:
                    val = str(filtered_data[field]).lower().strip()
                    filtered_data[field] = val in ["true", "1", "yes", "active", "y"]

            # 5. Handle List fields (e.g., images)
            list_fields = ["images"]
            for field in list_fields:
                if field in filtered_data:
                    val = filtered_data[field]
                    if isinstance(val, str) and val.strip():
                        filtered_data[field] = [item.strip() for item in val.split(",") if item.strip()]
                    elif val is None:
                        filtered_data[field] = []

            # 6. Handle date and string conversions (str expected in model)
            string_fields = ["barcode", "qr_code", "supplier_contact", "medicine_id", "batch_id", "mfd_date", "expiry_date", "last_restocked_date", "category", "manufacturer", "dosage_form", "strength"]
            for field in string_fields:
                if field in filtered_data:
                    val = filtered_data[field]
                    if isinstance(val, (datetime,)):
                        filtered_data[field] = val.strftime("%Y-%m-%d")
                    elif not isinstance(val, str) and val is not None:
                        # Convert numeric types to string (avoiding .0 for integers)
                        if isinstance(val, float) and val.is_integer():
                            filtered_data[field] = str(int(val))
                        else:
                            filtered_data[field] = str(val)
            
            # 7. Instantiate and save model
            med = Medication(**filtered_data)
            await engine.save(med)
            medications.append(med)
            
        except Exception as e:
            # Log specific details to help debugging
            med_name = data.get('name', f"Row {i+1}")
            print(f"ERROR: Bulk creation failed for medication '{med_name}': {e}")
            continue
            
    return medications


async def bulk_delete_medications(engine: AIOEngine, vendor_id: str, medication_ids: List[str]) -> int:
    """
    Bulk delete medications for a specific vendor.
    """
    object_ids = [ObjectId(mid) for mid in medication_ids]
    query = [
        Medication.id.in_(object_ids),
        Medication.vendor_id == vendor_id
    ]
    
    # Odmantic doesn't have a direct bulk delete by query in the same way as PyMongo,
    # so we find and then delete, or use the engine's collection directly for efficiency.
    collection = engine.get_collection(Medication)
    result = await collection.delete_many({
        "_id": {"$in": object_ids},
        "vendor_id": vendor_id
    })
    
    return result.deleted_count

