"""
Review Service
CRUD operations for vendor reviews, including listing, replying, and status management.
"""
from datetime import datetime
from typing import Optional, List
from odmantic import AIOEngine
from bson import ObjectId
from fastapi import HTTPException, status
import logging

from vendor.models.review import Review
from core.enums import ReviewStatus

logger = logging.getLogger(__name__)


# ============================================
# Create Review
# ============================================

async def create_review(
    engine: AIOEngine,
    vendor_id: str,
    review_by: str,
    booking_id: str,
    care_professional_id: str,
    review_text: str,
    rating: float,
    vertical_id: Optional[str] = None,
    date: Optional[datetime] = None,
) -> Review:
    """Create a new review for a vendor."""
    review = Review(
        vendor_id=vendor_id,
        review_by=review_by,
        booking_id=booking_id,
        care_professional_id=care_professional_id,
        vertical_id=vertical_id,
        review_text=review_text,
        rating=rating,
        date=date or datetime.utcnow(),
        status=ReviewStatus.NEEDS_RESPONSE,
    )
    await engine.save(review)
    logger.info(f"✅ New review created for vendor {vendor_id} by {review_by}")
    return review


# ============================================
# Get Reviews
# ============================================

async def get_vendor_reviews(
    engine: AIOEngine,
    vendor_id: str,
    vertical_id: Optional[str] = None,
    status_filter: Optional[ReviewStatus] = None,
    care_professional_id: Optional[str] = None,
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    limit: Optional[int] = None,
    skip: int = 0,
) -> tuple[List[Review], int]:
    """Get all reviews for a vendor with optional filters."""

    query: dict = {"vendor_id": vendor_id}

    if vertical_id:
        query["vertical_id"] = vertical_id

    if status_filter:
        query["status"] = status_filter.value

    if care_professional_id:
        query["care_professional_id"] = care_professional_id

    if min_rating is not None or max_rating is not None:
        rating_q: dict = {}
        if min_rating is not None:
            rating_q["$gte"] = min_rating
        if max_rating is not None:
            rating_q["$lte"] = max_rating
        query["rating"] = rating_q

    collection = engine.get_collection(Review)
    total = await collection.count_documents(query)
    
    cursor = collection.find(query).sort("created_at", -1).skip(skip)
    if limit is not None:
        cursor = cursor.limit(limit)
    
    raw_reviews = await cursor.to_list(length=limit if limit is not None else total)

    reviews = []
    for doc in raw_reviews:
        doc["id"] = doc.pop("_id")
        if "vertical_id" not in doc:
            doc["vertical_id"] = None
        reviews.append(Review.model_construct(**doc))

    return reviews, total


async def get_review_by_id(
    engine: AIOEngine,
    vendor_id: str,
    review_id: str,
) -> Review:
    """Get a single review by ID, ensuring it belongs to the vendor."""
    raw = await engine.get_collection(Review).find_one({
        "_id": ObjectId(review_id),
        "vendor_id": vendor_id,
    })

    if not raw:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found or access denied",
        )

    raw["id"] = raw.pop("_id")
    if "vertical_id" not in raw:
        raw["vertical_id"] = None
    return Review.model_construct(**raw)


# ============================================
# Reply to Review
# ============================================

async def reply_to_review(
    engine: AIOEngine,
    vendor_id: str,
    review_id: str,
    reply_text: str,
) -> Review:
    """Add or update the vendor's reply to a review."""
    review = await get_review_by_id(engine, vendor_id, review_id)

    now = datetime.utcnow()
    await engine.get_collection(Review).update_one(
        {"_id": ObjectId(review_id)},
        {"$set": {
            "reply_text": reply_text,
            "status": ReviewStatus.RESPONDED.value,
            "updated_at": now,
        }},
    )

    review = await get_review_by_id(engine, vendor_id, review_id)
    logger.info(f"✅ Vendor {vendor_id} replied to review {review_id}")
    return review


# ============================================
# Update Review Status
# ============================================

async def update_review_status(
    engine: AIOEngine,
    vendor_id: str,
    review_id: str,
    new_status: ReviewStatus,
) -> Review:
    """Update the status of a review (e.g., flag or archive)."""
    review = await get_review_by_id(engine, vendor_id, review_id)

    now = datetime.utcnow()
    await engine.get_collection(Review).update_one(
        {"_id": ObjectId(review_id)},
        {"$set": {
            "status": new_status.value,
            "updated_at": now,
        }},
    )

    review = await get_review_by_id(engine, vendor_id, review_id)
    logger.info(f"🔄 Review {review_id} status updated to {new_status}")
    return review


# ============================================
# Analytics / Summary
# ============================================

async def get_review_summary(
    engine: AIOEngine,
    vendor_id: str,
    vertical_id: Optional[str] = None,
) -> dict:
    """Get aggregate review stats for a vendor including star breakdown and response rate."""
    collection = engine.get_collection(Review)

    match_q = {"vendor_id": vendor_id}
    if vertical_id:
        match_q["vertical_id"] = vertical_id

    pipeline = [
        {"$match": match_q},
        {
            "$group": {
                "_id": None,
                "total_reviews": {"$sum": 1},
                "average_rating": {"$avg": "$rating"},
                "responded_count": {
                    "$sum": {
                        "$cond": [{"$eq": ["$status", ReviewStatus.RESPONDED.value]}, 1, 0]
                    }
                },
                "stars_5": { "$sum": { "$cond": [{"$eq": ["$rating", 5]}, 1, 0] } },
                "stars_4": { "$sum": { "$cond": [{"$and": [{"$gte": ["$rating", 4]}, {"$lt": ["$rating", 5]}]}, 1, 0] } },
                "stars_3": { "$sum": { "$cond": [{"$and": [{"$gte": ["$rating", 3]}, {"$lt": ["$rating", 4]}]}, 1, 0] } },
                "stars_2": { "$sum": { "$cond": [{"$and": [{"$gte": ["$rating", 2]}, {"$lt": ["$rating", 3]}]}, 1, 0] } },
                "stars_1": { "$sum": { "$cond": [{"$and": [{"$gte": ["$rating", 1]}, {"$lt": ["$rating", 2]}]}, 1, 0] } },
            }
        },
    ]

    results = await collection.aggregate(pipeline).to_list(length=1)
    if not results:
        return {
            "total_reviews": 0,
            "average_rating": 0.0,
            "response_rate": 0,
            "rating_breakdown": {
                "5": 0, "4": 0, "3": 0, "2": 0, "1": 0
            }
        }

    r = results[0]
    total = r.get("total_reviews", 0)
    responded = r.get("responded_count", 0)
    
    return {
        "total_reviews": total,
        "average_rating": round(r.get("average_rating", 0.0), 2),
        "response_rate": round((responded / total * 100), 2) if total > 0 else 0,
        "rating_breakdown": {
            "5": r.get("stars_5", 0),
            "4": r.get("stars_4", 0),
            "3": r.get("stars_3", 0),
            "2": r.get("stars_2", 0),
            "1": r.get("stars_1", 0),
        }
    }
