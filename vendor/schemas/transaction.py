from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from core.enums import TransactionStatus


class TransactionCreateRequest(BaseModel):
    invoice_id: str
    booking_id: str
    customer_id: str
    amount: float
    status: TransactionStatus = TransactionStatus.PENDING
    payment_method: Optional[str] = None       # e.g. CASH, UPI, CARD, ONLINE
    payment_reference: Optional[str] = None    # UPI ID, card last4, gateway ref
    notes: Optional[str] = None                # Vendor notes about this payment
    date: Optional[str] = None
    time: Optional[str] = None


class TransactionUpdateRequest(BaseModel):
    status: Optional[TransactionStatus] = None
    amount: Optional[float] = None


class TransactionResponse(BaseModel):
    id: str
    vendor_id: str
    invoice_id: str
    booking_id: str
    customer_id: str
    amount: float
    status: TransactionStatus
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
    date: str
    time: str
    created_at: datetime
    updated_at: datetime


class TransactionListResponse(BaseModel):
    transactions: List[TransactionResponse]
    total: int
