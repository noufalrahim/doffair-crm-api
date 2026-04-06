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
    search: Optional[str] = None,
    secondary_engine: Optional[AIOEngine] = None,
) -> tuple[List[Review], int]:
    """Get all reviews for a vendor with optional filters and name search."""

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

    # Handle Search (Cross-Database Search)
    if search and secondary_engine:
        import re
        search_regex = {"$regex": re.escape(search), "$options": "i"}
        
        # 1. Search in Secondary DB (users + userInfo)
        user_coll = secondary_engine.database.get_collection("users")
        user_info_coll = secondary_engine.database.get_collection("userInfo")
        
        matching_users = await user_coll.find({
            "$or": [
                {"username": search_regex},
                {"phoneNumber": search_regex},
                {"phone": search_regex},
                {"email": search_regex}
            ]
        }).to_list(length=100)
        
        matching_user_infos = await user_info_coll.find({
            "name": search_regex
        }).to_list(length=100)
        
        user_ids = {str(u["_id"]) for u in matching_users}
        for ui in matching_user_infos:
            u_ref = ui.get("userId")
            if u_ref:
                from bson import DBRef
                if isinstance(u_ref, DBRef):
                    user_ids.add(str(u_ref.id))
                else:
                    user_ids.add(str(u_ref))
        
        if user_ids:
            query["review_by"] = {"$in": list(user_ids)}
        else:
            # If search term provided but no users found, return empty results
            return [], 0

    # Use engine.find() to properly initialize Review instances and avoid FieldProxy errors
    reviews = await engine.find(
        Review,
        query,
        sort=Review.created_at.desc(),
        limit=limit,
        skip=skip
    )
    total = await engine.count(Review, query)

    # Data Enrichment (Fetch Names/Images from Secondary DB)
    if reviews and secondary_engine:
        unique_uids = {r.review_by for r in reviews if r.review_by}
        if unique_uids:
            try:
                from bson import DBRef
                
                # 1. Prepare mapping structures
                info_map = {}
                oid_list = []
                uid_to_oid = {}
                
                for uid in unique_uids:
                    if ObjectId.is_valid(uid):
                        oid = ObjectId(uid)
                        oid_list.append(oid)
                        uid_to_oid[uid] = oid
                    else:
                        uid_to_oid[uid] = uid # Keep as string if not valid ObjectId

                # 2. Fetch from 'users' collection (username, firstName fallbacks)
                user_coll = secondary_engine.database.get_collection("users")
                user_docs = await user_coll.find({
                    "_id": {"$in": oid_list}
                }).to_list(length=len(oid_list))
                
                for u in user_docs:
                    u_id_str = str(u["_id"])
                    info_map[u_id_str] = {
                        "name": u.get("username") or u.get("firstName") or "Anonymous",
                        "image": None
                    }

                # 3. Fetch from 'userInfo' collection (actual full names and profile images)
                user_info_coll = secondary_engine.database.get_collection("userInfo")
                
                # Prepare exhaustive query for userInfo (matches ObjectId, string, or DBRef)
                potential_user_ids = []
                for oid in oid_list:
                    potential_user_ids.extend([oid, str(oid), DBRef("users", oid)])
                
                user_info_docs = await user_info_coll.find({
                    "userId": {"$in": potential_user_ids}
                }).to_list(length=len(unique_uids))
                
                for ui in user_info_docs:
                    u_ref = ui.get("userId")
                    # Extract the ID string from DBRef or raw ID
                    u_id_str = str(u_ref.id if hasattr(u_ref, 'id') else u_ref)
                    
                    if u_id_str not in info_map:
                        info_map[u_id_str] = {"name": "Anonymous", "image": None}
                    
                    if ui.get("name"):
                        info_map[u_id_str]["name"] = ui.get("name")
                    
                    # Preference for images: image > profileImage > avatar > photo
                    img = ui.get("image") or ui.get("profileImage") or ui.get("avatar") or ui.get("photo")
                    if img:
                        info_map[u_id_str]["image"] = img
                
                # 4. Attach to Review objects
                for r in reviews:
                    uid = str(r.review_by)
                    if uid in info_map:
                        setattr(r, "reviewer_name", info_map[uid]["name"])
                        setattr(r, "reviewer_image", info_map[uid]["image"])
                    else:
                        # Final fallback if absolutely nothing found in Secondary DB
                        setattr(r, "reviewer_name", "Anonymous User")
                        
            except Exception as e:
                logger.error(f"❌ Error enriching reviews: {e}")
                import traceback
                logger.error(traceback.format_exc())
                pass

    return reviews, total


async def get_review_by_id(
    engine: AIOEngine,
    vendor_id: str,
    review_id: str,
) -> Review:
    """Get a single review by ID, ensuring it belongs to the vendor."""
    review = await engine.find_one(Review, {
        Review.id: ObjectId(review_id),
        Review.vendor_id: vendor_id,
    })

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found or access denied",
        )

    return review


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
