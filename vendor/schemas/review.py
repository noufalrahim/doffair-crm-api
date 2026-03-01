from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from core.enums import ReviewStatus


class ReviewCreateRequest(BaseModel):
    review_by: str = Field(..., description="User ID of the reviewer")
    booking_id: str
    care_professional_id: str
    vertical_id: Optional[str] = None
    review_text: str
    rating: float = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    date: Optional[datetime] = None


class ReviewUpdateRequest(BaseModel):
    review_text: Optional[str] = None
    reply_text: Optional[str] = Field(None, description="Vendor reply to the review")
    rating: Optional[float] = Field(None, ge=1, le=5)
    status: Optional[ReviewStatus] = None


class ReviewResponse(BaseModel):
    id: str
    vendor_id: str
    review_by: str
    booking_id: str
    care_professional_id: str
    vertical_id: Optional[str] = None
    review_text: str
    reply_text: Optional[str] = None
    rating: float
    status: ReviewStatus
    date: str
    created_at: str
    updated_at: str

    # Enriched fields
    reviewer_name: Optional[str] = None
    reviewer_email: Optional[str] = None
    reviewer_phone: Optional[str] = None
    care_professional_name: Optional[str] = None
