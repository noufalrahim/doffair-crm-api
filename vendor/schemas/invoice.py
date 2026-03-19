from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from core.enums import InvoiceStatus


class InvoiceItemSchema(BaseModel):
    """Line item for an invoice"""
    name: str
    quantity: int = Field(1, gt=0)
    unit_price: float = Field(0.0, ge=0)
    subtotal: float = Field(0.0, ge=0)


class InvoiceCreateRequest(BaseModel):
    """Request to create an itemized invoice"""
    customer_id: str
    booking_id: Optional[str] = None
    vertical_id: Optional[str] = None
    due_date: Optional[datetime] = None
    
    items: List[InvoiceItemSchema] = []
    notes: Optional[str] = None
    tax_amount: float = 0.0
    discount_amount: float = 0.0
    
    # Grand total can be provided or calculated
    grand_total: Optional[float] = Field(None, gt=0)


class InvoiceUpdateRequest(BaseModel):
    """Update invoice details"""
    due_date: Optional[datetime] = None
    grand_total: Optional[float] = Field(None, gt=0)
    paid_amount: Optional[float] = Field(None, ge=0)
    status: Optional[InvoiceStatus] = None
    notes: Optional[str] = None


class InvoiceResponse(BaseModel):
    """Itemized invoice response"""
    id: str
    invoice_number: str
    invoice_date: datetime
    due_date: Optional[datetime] = None
    customer_id: str
    booking_id: Optional[str] = None
    vertical_id: Optional[str] = None
    
    items: List[InvoiceItemSchema] = []
    notes: Optional[str] = None
    tax_amount: float = 0.0
    discount_amount: float = 0.0
    grand_total: float = 0.0
    paid_amount: float = 0.0
    balance_due: float = 0.0
    status: InvoiceStatus
    created_at: datetime
    updated_at: datetime


class InvoiceStatisticsResponse(BaseModel):
    """Financial statistics for a vendor/vertical"""
    total_earnings: float
    total_bookings: int
    total_generated: int
    total_paid: int
    total_refunded: int
    total_overdue: int


class InvoiceListResponse(BaseModel):
    """List of itemized invoices"""
    total: int
    invoices: List[InvoiceResponse]

