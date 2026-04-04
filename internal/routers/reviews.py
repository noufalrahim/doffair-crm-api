from fastapi import APIRouter, Depends, status
from odmantic import AIOEngine
import logging

from core.database import get_engine
from vendor.services import review_service
from internal.schemas.review import InternalReviewCreateRequest
from utils.response import success_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/reviews", tags=["Internal"])

def _serialize(review):
    """Helper to serialize a Review model to a dict for API response."""
    return {
        "id": str(review.id),
        "vendor_id": str(review.vendor_id),
        "review_by": review.review_by,
        "booking_id": review.booking_id,
        "care_professional_id": review.care_professional_id,
        "vertical_id": getattr(review, "vertical_id", None),
        "review_text": review.review_text,
        "reply_text": review.reply_text,
        "rating": review.rating,
        "status": review.status.value if hasattr(review.status, 'value') else review.status,
        "date": review.date.isoformat(),
        "created_at": review.created_at.isoformat(),
        "updated_at": review.updated_at.isoformat(),
    }

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_internal_review(
    body: InternalReviewCreateRequest,
    engine: AIOEngine = Depends(get_engine),
):
    """
    Internal endpoint to sync reviews from the user app (Java server).
    This endpoint does not require vendor JWT authentication.
    """
    logger.info(f"Syncing internal review for booking {body.booking_id}")
    
    review = await review_service.create_review(
        engine=engine,
        vendor_id=body.vendor_id,
        review_by=body.review_by,
        booking_id=body.booking_id,
        care_professional_id=body.care_professional_id,
        vertical_id=body.vertical_id,
        review_text=body.review_text,
        rating=body.rating,
        date=body.date,
    )
    
    return success_response(
        data=_serialize(review),
        message="Internal review synced successfully"
    )
