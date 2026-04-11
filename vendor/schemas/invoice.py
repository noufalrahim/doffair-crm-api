from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from core.enums import InvoiceStatus


class InvoiceItemSchema(BaseModel):
    """Line item for an invoice"""
    name: str
    hsn_sac: Optional[str] = None
    mrp: Optional[float] = 0.0
    quantity: int = Field(1, gt=0)
    unit_price: float = Field(0.0, ge=0)
    discount_amount: float = Field(0.0, ge=0)
    taxable_value: float = Field(0.0, ge=0)
    tax_rate: float = Field(0.0, ge=0)
    tax_amount: float = Field(0.0, ge=0)
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
    rounding_off: float = 0.0
    
    # Grand total can be provided or calculated
    grand_total: Optional[float] = Field(None, gt=0)


class InvoiceGenerateRequest(BaseModel):
    """Request to generate an invoice from a booking"""
    booking_id: str
    due_days: Optional[int] = 30
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    auto_send: bool = True
    
    amount_paid: Optional[float] = None
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    payment_notes: Optional[str] = None


class InvoiceSendRequest(BaseModel):
    """Request to manually send an invoice"""
    channels: List[str] = ["email"]
    notes: Optional[str] = None


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
    
    vendor_name: Optional[str] = None
    vendor_address: Optional[str] = None
    vendor_gstin: Optional[str] = None
    vendor_phone: Optional[str] = None
    
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_pincode: Optional[str] = None
    
    items: List[InvoiceItemSchema] = []
    notes: Optional[str] = None
    tax_amount: float = 0.0
    discount_amount: float = 0.0
    rounding_off: float = 0.0
    grand_total: float = 0.0
    grand_total_words: Optional[str] = None
    paid_amount: float = 0.0
    balance_due: float = 0.0
    tax_details: dict = {}
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

