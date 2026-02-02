from datetime import datetime
from odmantic import Model, Field
from typing import Optional
from core.enums import PaymentStatus


class Payment(Model):
    """
    Payment tracking for bookings
    """
    booking_id: str
    user_id: str
    vendor_id: str
    
    # Payment details
    amount: float
    payment_method: str = "razorpay"  # razorpay, stripe, cash, etc.
    

    payment_gateway_order_id: Optional[str] = None   
    payment_gateway_payment_id: Optional[str] = None 
    payment_gateway_signature: Optional[str] = None  
    
    # Status tracking
    status: PaymentStatus = PaymentStatus.PENDING
    
    # Timestamps
    initiated_at: datetime = Field(default_factory=datetime.utcnow)
    paid_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    
    # Refund details
    refund_amount: Optional[float] = None
    refund_reason: Optional[str] = None
    refund_gateway_id: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "collection": "payments",
        "indexes": [
            {"fields": ["booking_id"]},
            {"fields": ["user_id"]},
            {"fields": ["vendor_id"]},
            {"fields": ["payment_gateway_order_id"]},
            {"fields": ["payment_gateway_payment_id"]},
            {"fields": ["status"]},
        ],
    }
