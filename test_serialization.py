import asyncio
from odmantic import AIOEngine, ObjectId
import datetime
from vendor.models.review import Review
from vendor.services import review_service
from core.database import get_engine
import json
from motor.motor_asyncio import AsyncIOMotorClient

# Mock a Review instance if we can't connect to DB, but we should try to connect
MONGO_URI = "mongodb+srv://doffair_dev:yTwgZQf2t3XiSXos@development-cluster.9w53x.mongodb.net/?retryWrites=true&w=majority&appName=development-cluster"

def _serialize(review: Review) -> dict:
    """Helper from vendor/routers/reviews.py"""
    # This is what was causing the error if vertical_id was a FieldProxy
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

async def run_test():
    print("--- 🔍 Testing Review Serialization ---")
    
    # Setup engine manually for script
    client = AsyncIOMotorClient(MONGO_URI)
    engine = AIOEngine(client=client, database="doffair_vendors_new")
    
    # Test Vendor ID from logs
    vendor_id = "69932ac266da12767de69139"
    vertical_id = "69522b6ce6a07c46de0f88d7"
    
    print(f"📡 Fetching reviews for vendor {vendor_id} and vertical {vertical_id}...")
    reviews, total = await review_service.get_vendor_reviews(
        engine=engine,
        vendor_id=vendor_id,
        vertical_id=vertical_id,
        limit=5
    )
    
    print(f"✅ Found {len(reviews)} reviews (Total: {total})")
    
    for i, r in enumerate(reviews):
        try:
            serialized = _serialize(r)
            print(f"📦 Review {i+1} serialized successfully: {serialized['id']}")
            # Try to json dumps to be 100% sure
            json.dumps(serialized)
        except Exception as e:
            print(f"❌ FAILED to serialize review {i+1}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test())
