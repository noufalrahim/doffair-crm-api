from datetime import datetime
from odmantic import Model, Field, EmbeddedModel
from typing import Optional, List
from core.enums import InvoiceStatus


class InvoiceItem(EmbeddedModel):
    """
    Line item for an invoice
    """
    name: str
    quantity: int = 1
    unit_price: float = 0.0
    subtotal: float = 0.0


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
    
    items: List[InvoiceItem] = []
    notes: Optional[str] = None
    
    tax_amount: float = 0.0
    discount_amount: float = 0.0
    grand_total: float = 0.0
    paid_amount: float = 0.0
    balance_due: float = 0.0
    
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

