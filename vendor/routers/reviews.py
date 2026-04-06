from fastapi import APIRouter, Depends, HTTPException, status, Query
from odmantic import AIOEngine, ObjectId
from typing import List, Optional
from datetime import datetime

from core.database import get_engine, get_secondary_engine
from core.security import get_current_vendor
from vendor.models.review import Review
from core.enums import ReviewStatus
from vendor.schemas.review import ReviewCreateRequest, ReviewResponse, ReviewUpdateRequest
from vendor.services import review_service
from utils.response import success_response
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vendors/reviews", tags=["Reviews"])

def _serialize(review: Review) -> dict:
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
        
        # Enriched fields from service
        "reviewer_name": getattr(review, "reviewer_name", None),
        "reviewer_image": getattr(review, "reviewer_image", None),
    }


# ============================================
# POST /vendor/reviews/
# ============================================

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_review(
    body: ReviewCreateRequest,
    token: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine),
):
    """Post a new review for a vendor."""
    vendor_id = token.get("vendor_id")
    review = await review_service.create_review(
        engine=engine,
        vendor_id=vendor_id,
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
        message="Review created successfully"
    )


# ============================================
# GET /vendor/reviews/
# ============================================

@router.get(
    "/",
    summary="List Vendor Reviews",
    description="Returns reviews for the authenticated vendor. **vertical_id is required.**",
)
async def list_reviews(
    vertical_id: str = Query(..., description="ID of the vertical to filter reviews by", example="69522b6ce6a07c46de0f88d7"),
    search: Optional[str] = Query(None, description="Search by customer name"),
    status_filter: Optional[ReviewStatus] = Query(None, description="Filter by review status"),
    care_professional_id: Optional[str] = Query(None, description="Filter by care professional ID"),
    min_rating: Optional[float] = Query(None, ge=1, le=5, description="Minimum rating (1-5)"),
    max_rating: Optional[float] = Query(None, ge=1, le=5, description="Maximum rating (1-5)"),
    limit: int = Query(50, ge=1, le=200, description="Max results to return"),
    skip: int = Query(0, ge=0, description="Results to skip"),
    token: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine),
    secondary_engine: AIOEngine = Depends(get_secondary_engine),
):
    """List reviews for the authenticated vendor filtered by vertical (required)."""
    vendor_id = token.get("vendor_id")
    reviews, total = await review_service.get_vendor_reviews(
        engine=engine,
        secondary_engine=secondary_engine,
        vendor_id=vendor_id,
        vertical_id=vertical_id,
        search=search,
        status_filter=status_filter,
        care_professional_id=care_professional_id,
        min_rating=min_rating,
        max_rating=max_rating,
        limit=limit,
        skip=skip,
    )
    return success_response(
        data={"total": total, "reviews": [_serialize(r) for r in reviews]}
    )



# ============================================
# GET /vendor/reviews/summary
# ============================================

@router.get(
    "/summary",
    summary="Get Review Summary",
    description="Returns aggregate stats (average rating, total reviews, rating breakdown, response rate) for the authenticated vendor's reviews, filtered by vertical.",
)
async def review_summary(
    vertical_id: str = Query(..., description="ID of the vertical to filter summary by", example="69522b6ce6a07c46de0f88d7"),
    token: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine),
):
    """Get aggregate review stats for a specific vertical."""
    vendor_id = token.get("vendor_id")
    summary = await review_service.get_review_summary(
        engine=engine, 
        vendor_id=vendor_id,
        vertical_id=vertical_id
    )
    return success_response(data=summary)


# ============================================
# GET /vendor/reviews/{review_id}
# ============================================

@router.get("/{review_id}")
async def get_review(
    review_id: str,
    token: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine),
):
    """Get a single review by ID."""
    vendor_id = token.get("vendor_id")
    review = await review_service.get_review_by_id(engine=engine, vendor_id=vendor_id, review_id=review_id)
    return success_response(data=_serialize(review))


# ============================================
# POST /vendor/reviews/{review_id}/reply
# ============================================

@router.post("/{review_id}/reply")
async def reply_to_review(
    review_id: str,
    body: dict,
    token: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine),
):
    """Reply to a review. Body: { \"reply_text\": \"...\" }"""
    vendor_id = token.get("vendor_id")
    reply_text = body.get("reply_text", "").strip()
    if not reply_text:
        return success_response(message="reply_text is required", success=False)
    
    review = await review_service.reply_to_review(
        engine=engine,
        vendor_id=vendor_id,
        review_id=review_id,
        reply_text=reply_text,
    )
    return success_response(
        data=_serialize(review),
        message="Reply posted successfully"
    )


# ============================================
# PATCH /vendor/reviews/{review_id}/status
# ============================================

@router.patch("/{review_id}/status")
async def update_review_status(
    review_id: str,
    body: dict,
    token: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine),
):
    """Update review status. Body: { \"status\": \"FLAGGED\" | \"ARCHIVED\" | ... }"""
    vendor_id = token.get("vendor_id")
    raw_status = body.get("status")
    if not raw_status:
        return success_response(message="status is required", success=False)
    try:
        new_status = ReviewStatus(raw_status)
    except ValueError:
        return success_response(
            message=f"Invalid status. Valid values: {[e.value for e in ReviewStatus]}",
            success=False
        )
    review = await review_service.update_review_status(
        engine=engine,
        vendor_id=vendor_id,
        review_id=review_id,
        new_status=new_status,
    )
    return success_response(
        data=_serialize(review),
        message="Status updated successfully"
    )
