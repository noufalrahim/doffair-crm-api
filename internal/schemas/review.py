from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class InternalReviewCreateRequest(BaseModel):
    vendor_id: str = Field(..., description="ID of the vendor (service provider)")
    review_by: str = Field(..., description="User ID of the reviewer")
    booking_id: str
    care_professional_id: str
    vertical_id: Optional[str] = None
    review_text: str
    rating: float = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    date: Optional[datetime] = None
