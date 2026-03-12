from datetime import datetime
from odmantic import Model, Field
from typing import Optional
from core.enums import TransactionStatus


class Transaction(Model):
    """
    Transaction document for tracking payments against invoices
    """
    vendor_id: str
    invoice_id: str
    booking_id: str
    customer_id: str
    
    amount: float = 0.0
    status: TransactionStatus = TransactionStatus.PENDING
    
    date: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d"))
    time: str = Field(default_factory=lambda: datetime.utcnow().strftime("%H:%M:%S"))
    
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "collection": "transactions",
        "indexes": [
            {"fields": ["vendor_id"]},
            {"fields": ["invoice_id"]},
            {"fields": ["booking_id"]},
            {"fields": ["customer_id"]},
            {"fields": ["status"]},
        ],
    }
