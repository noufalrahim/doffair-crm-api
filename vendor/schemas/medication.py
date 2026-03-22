from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MedicationCreate(BaseModel):
    medicine_id: Optional[str] = Field(None, description="UUID / SKU of the medicine")
    name: str = Field(..., description="Brand name of the medication")
    brand_name: Optional[str] = Field(None, description="Brand name if different from name")
    generic_composition: Optional[str] = Field(None, description="Generic composition (e.g., Amoxicillin + Clavulanate)")
    vertical_id: str = Field(..., description="ID of the vertical (e.g., pharmacy)")
    vendor_id: Optional[str] = Field(None, description="Optional ID of the vendor")
    description: Optional[str] = Field(None, description="Optional description of the medication")
    category: str = Field(..., description="Category of the medicine (Antibiotic, NSAID, etc.)")
    dosage_form: Optional[str] = Field(None, description="Dosage form (Tablet, Syrup, etc.)")
    strength: Optional[str] = Field(None, description="Strength (e.g., 50 mg, 1.5 mg/ml)")
    is_prescription_required: bool = Field(False, description="Whether prescription is required")
    
    indications: Optional[str] = Field(None, description="What it treats")
    contraindications: Optional[str] = Field(None, description="Contraindications")
    side_effects: Optional[str] = Field(None, description="Side effects")
    drug_interactions: Optional[str] = Field(None, description="Drug interactions")
    storage_instructions: Optional[str] = Field(None, description="Storage instructions")
    schedule_class: Optional[str] = Field(None, description="Regulated schedule class")
    barcode: Optional[str] = Field(None, description="Barcode")
    qr_code: Optional[str] = Field(None, description="QR Code")
    
    quantity_to_give: str = Field(..., description="Quantity to give (e.g., 1 strip, 1 bottle)")
    stock_quantity: int = Field(..., description="Current stock quantity")
    unit: str = Field(..., description="Unit of measurement (e.g., tablets, ml)")
    base_price: float = Field(..., description="Original base price")
    purchase_price: Optional[float] = Field(None, description="Purchase price")
    selling_price: Optional[float] = Field(None, description="Selling price")
    
    batch_id: str = Field(..., description="Batch identifier")
    manufacturer: str = Field(..., description="Manufacturer name")
    supplier_name: Optional[str] = Field(None, description="Supplier name")
    supplier_contact: Optional[str] = Field(None, description="Supplier contact")
    
    mfd_date: str = Field(..., description="Manufacturing date")
    expiry_date: str = Field(..., description="Expiry date")
    last_restocked_date: Optional[str] = Field(None, description="Last restocked date")
    
    pack_size: Optional[str] = Field(None, description="Pack size (e.g., 10 tablets per strip)")
    units_per_pack: Optional[int] = Field(None, description="Units per pack")
    reorder_level: Optional[int] = Field(None, description="Reorder level")
    reorder_quantity: Optional[int] = Field(None, description="Reorder quantity")
    location: Optional[str] = Field(None, description="Shelf/rack/bin location")
    
    near_expiry_flag: bool = Field(False, description="Flag for near expiry")
    is_expired: bool = Field(False, description="Flag for expired medication")
    
    images: Optional[list[str]] = Field(None, description="Optional list of image URLs")
    image_url: Optional[str] = Field(None, description="Primary image URL")
    
    status: str = Field("Active", description="Status (Active/Inactive)")
    
    dosage: Optional[str] = Field(None, description="Dosage (e.g., 500mg, 5ml)")
    frequency: Optional[str] = Field(None, description="Frequency (e.g., Once a day, Twice a day)")
    duration: Optional[str] = Field(None, description="Duration (e.g., 5 days, 1 week)")
    notes: Optional[str] = Field("", description="Optional notes about the medication")

class MedicationUpdate(BaseModel):
    medicine_id: Optional[str] = None
    name: Optional[str] = None
    brand_name: Optional[str] = None
    generic_composition: Optional[str] = None
    vertical_id: Optional[str] = None
    vendor_id: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    dosage_form: Optional[str] = None
    strength: Optional[str] = None
    is_prescription_required: Optional[bool] = None
    
    indications: Optional[str] = None
    contraindications: Optional[str] = None
    side_effects: Optional[str] = None
    drug_interactions: Optional[str] = None
    storage_instructions: Optional[str] = None
    schedule_class: Optional[str] = None
    barcode: Optional[str] = None
    qr_code: Optional[str] = None
    
    quantity_to_give: Optional[str] = None
    stock_quantity: Optional[int] = None
    unit: Optional[str] = None
    base_price: Optional[float] = None
    purchase_price: Optional[float] = None
    selling_price: Optional[float] = None
    
    batch_id: Optional[str] = None
    manufacturer: Optional[str] = None
    supplier_name: Optional[str] = None
    supplier_contact: Optional[str] = None
    
    mfd_date: Optional[str] = None
    expiry_date: Optional[str] = None
    last_restocked_date: Optional[str] = None
    
    pack_size: Optional[str] = None
    units_per_pack: Optional[int] = None
    reorder_level: Optional[int] = None
    reorder_quantity: Optional[int] = None
    location: Optional[str] = None
    
    near_expiry_flag: Optional[bool] = None
    is_expired: Optional[bool] = None
    
    images: Optional[list[str]] = None
    image_url: Optional[str] = None
    
    status: Optional[str] = None
    is_active: Optional[bool] = None

class MedicationResponse(BaseModel):
    id: str
    medicine_id: Optional[str] = None
    vertical_id: str
    vendor_id: Optional[str] = None
    name: str
    brand_name: Optional[str] = None
    generic_composition: Optional[str] = None
    description: Optional[str] = None
    category: str
    dosage_form: Optional[str] = None
    strength: Optional[str] = None
    is_prescription_required: bool
    
    indications: Optional[str] = None
    contraindications: Optional[str] = None
    side_effects: Optional[str] = None
    drug_interactions: Optional[str] = None
    storage_instructions: Optional[str] = None
    schedule_class: Optional[str] = None
    barcode: Optional[str] = None
    qr_code: Optional[str] = None
    
    quantity_to_give: str
    stock_quantity: int
    unit: str
    base_price: float
    purchase_price: Optional[float] = None
    selling_price: Optional[float] = None
    
    batch_id: str
    manufacturer: str
    supplier_name: Optional[str] = None
    supplier_contact: Optional[str] = None
    
    mfd_date: str
    expiry_date: str
    last_restocked_date: Optional[str] = None
    
    pack_size: Optional[str] = None
    units_per_pack: Optional[int] = None
    reorder_level: Optional[int] = None
    reorder_quantity: Optional[int] = None
    location: Optional[str] = None
    
    near_expiry_flag: bool
    is_expired: bool
    
    images: Optional[list[str]] = None
    image_url: Optional[str] = None
    
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "65f1a2b3c4d5e6f7a8b9c0d1",
                "vertical_id": "pharmacy_vertical_id",
                "vendor_id": "65f1a2b3c4d5e6f7a8b9c0d2",
                "name": "Paracetamol",
                "description": "Pain reliever and fever reducer",
                "category": "Analgesics",
                "quantity_to_give": "1 strip",
                "stock_quantity": 100,
                "unit": "tablets",
                "base_price": 50.0,
                "batch_id": "BAT12345",
                "manufacturer": "HealthCorp",
                "mfd_date": "2024-01-01",
                "expiry_date": "2026-01-01",
                "images": ["https://example.com/image.jpg"],
                "dosage": "500mg",
                "frequency": "Three times a day",
                "duration": "5 days",
                "notes": "Take after meals",
                "is_active": True,
                "created_at": "2024-03-11T10:00:00Z",
                "updated_at": "2024-03-11T10:00:00Z"
            }
        }

class MedicationListResponse(BaseModel):
    total: int
    medications: list[MedicationResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 1,
                "medications": [
                    {
                        "id": "65f1a2b3c4d5e6f7a8b9c0d1",
                        "vertical_id": "pharmacy_vertical_id",
                        "vendor_id": "65f1a2b3c4d5e6f7a8b9c0d2",
                        "name": "Paracetamol",
                        "category": "Analgesics",
                        "quantity_to_give": "1 strip",
                        "stock_quantity": 100,
                        "unit": "tablets",
                        "base_price": 50.0,
                        "batch_id": "BAT12345",
                        "manufacturer": "HealthCorp",
                        "mfd_date": "2024-01-01",
                        "expiry_date": "2026-01-01",
                        "is_active": True,
                        "created_at": "2024-03-11T10:00:00Z",
                        "updated_at": "2024-03-11T10:00:00Z"
                    }
                ]
            }
        }
