from datetime import datetime
from odmantic import Model, Field, EmbeddedModel
from typing import Optional, List
from core.enums import InvoiceStatus


class InvoiceItem(EmbeddedModel):
    """
    Line item for an invoice
    """
    name: str
    hsn_sac: Optional[str] = None
    mrp: Optional[float] = 0.0
    quantity: int = 1
    unit_price: float = 0.0
    discount_amount: float = 0.0
    taxable_value: float = 0.0
    tax_rate: float = 0.0  # Percentage (e.g., 18.0)
    tax_amount: float = 0.0
    subtotal: float = 0.0  # Total for this item (taxable_value + tax_amount)


class Invoice(Model):
    """
    Itemized Invoice document
    """
    vendor_id: str
    customer_id: str
    booking_id: Optional[str] = None
    vertical_id: Optional[str] = None
    
    invoice_number: str  # Generated: e.g., INV-0001-8372
    invoice_date: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None
    
    # Cached details for the invoice
    vendor_name: Optional[str] = None
    vendor_address: Optional[str] = None
    vendor_gstin: Optional[str] = None
    vendor_phone: Optional[str] = None
    
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_pincode: Optional[str] = None
    
    items: List[InvoiceItem] = []
    notes: Optional[str] = None
    
    tax_amount: float = 0.0
    discount_amount: float = 0.0
    rounding_off: float = 0.0
    grand_total: float = 0.0
    grand_total_words: Optional[str] = None
    paid_amount: float = 0.0
    balance_due: float = 0.0
    
    # Detailed tax breakdown (e.g., {"SGST 9%": 35.01, "CGST 9%": 35.01})
    tax_details: dict = {}
    
    status: InvoiceStatus = InvoiceStatus.DRAFT
    
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "collection": "invoices",
        "indexes": [
            {"fields": ["vendor_id"]},
            {"fields": ["customer_id"]},
            {"fields": ["booking_id"]},
            {"fields": ["invoice_number"], "unique": True},
            {"fields": ["status"]},
            {"fields": ["vertical_id"]},
        ],
    }

