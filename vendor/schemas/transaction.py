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
    date: str
    time: str
    created_at: datetime
    updated_at: datetime


class TransactionListResponse(BaseModel):
    transactions: List[TransactionResponse]
    total: int
