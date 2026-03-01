from odmantic import Model, Field
from typing import Optional
from datetime import datetime

from core.enums import ReviewStatus


class Review(Model):
    vendor_id: str
    review_by: str          # user_id of the reviewer
    booking_id: str
    care_professional_id: str
    vertical_id: Optional[str] = None

    review_text: str
    reply_text: Optional[str] = None
    rating: float           # 1.0 – 5.0

    status: ReviewStatus = ReviewStatus.NEEDS_RESPONSE
    date: datetime = Field(default_factory=datetime.utcnow)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "reviews",
        "indexes": [
            {"fields": ["vendor_id"]},
            {"fields": ["review_by"]},
            {"fields": ["booking_id"]},
            {"fields": ["care_professional_id"]},
            {"fields": ["vertical_id"]},
        ],
    }

