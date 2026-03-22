from odmantic import Model, Field
from datetime import datetime
from typing import Optional

class Medication(Model):
    """
    Medication master record managed by vendor
    """
    vendor_id: Optional[str] = None
    vertical_id: str
    medicine_id: Optional[str] = None # UUID / SKU
    name: str # Brand name used as name in original
    brand_name: Optional[str] = None
    generic_composition: Optional[str] = None
    description: Optional[str] = None
    category: str
    dosage_form: Optional[str] = None # Tablet, Syrup, etc.
    strength: Optional[str] = None # e.g., 50 mg
    is_prescription_required: bool = False
    
    # Static Data - Good to Have
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
    base_price: float # Original selling price
    purchase_price: Optional[float] = None
    selling_price: Optional[float] = None
    
    batch_id: str
    manufacturer: str
    supplier_name: Optional[str] = None
    supplier_contact: Optional[str] = None
    
    mfd_date: str
    expiry_date: str
    last_restocked_date: Optional[str] = None
    
    pack_size: Optional[str] = None # e.g., 10 tablets per strip
    units_per_pack: Optional[int] = None
    reorder_level: Optional[int] = None
    reorder_quantity: Optional[int] = None
    location: Optional[str] = None # shelf/rack/bin
    
    near_expiry_flag: bool = False
    is_expired: bool = False
    
    images: Optional[list[str]] = None
    image_url: Optional[str] = None
    
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    notes: str = ""
    
    is_active: bool = True
    status: str = "Active" # Active/Inactive
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "collection": "medications",
        "indexes": [
            {"fields": ["vendor_id"]},
            {"fields": ["vertical_id"]},
            {"fields": ["vendor_id", "name"]},
            {"fields": ["vertical_id", "name"]},
            {"fields": ["is_active"]},
        ],
    }
