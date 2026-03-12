from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from core.enums import InvoiceStatus


class InvoiceCreateRequest(BaseModel):
    """Request to create a simple invoice"""
    customer_id: str
    booking_id: Optional[str] = None
    vertical_id: Optional[str] = None
    due_date: Optional[datetime] = None
    grand_total: float = Field(..., gt=0)
    notes: Optional[str] = None


class InvoiceUpdateRequest(BaseModel):
    """Update invoice details"""
    due_date: Optional[datetime] = None
    grand_total: Optional[float] = Field(None, gt=0)
    paid_amount: Optional[float] = Field(None, ge=0)
    status: Optional[InvoiceStatus] = None


class InvoiceResponse(BaseModel):
    """Simplified invoice response"""
    id: str
    invoice_number: str
    invoice_date: datetime
    due_date: Optional[datetime] = None
    customer_id: str
    booking_id: Optional[str] = None
    vertical_id: Optional[str] = None
    grand_total: float
    paid_amount: float
    balance_due: float
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
    """List of simplified invoices"""
    total: int
    invoices: List[InvoiceResponse]
