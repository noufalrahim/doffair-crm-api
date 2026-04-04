import pymongo
import requests
import json
from datetime import datetime
import time

# Configuration
JAVA_API_URL = "http://localhost:8080/doffairapi/ratings"
BEARER_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJub3VmYWxyYWhpbTA0NDRAZ21haWwuY29tIiwiaWF0IjoxNzc1MDk3MTQzLCJleHAiOjIxMzUwOTcxNDN9.hfKvFuduBfM9TFlS4LOEED0sfLU0DJ-3DkZ1cS8JcP8"

# MongoDB Configuration
MONGO_URI = "mongodb+srv://doffair_dev:yTwgZQf2t3XiSXos@development-cluster.9w53x.mongodb.net/?retryWrites=true&w=majority&appName=development-cluster"
DB_NAME = "doffair_vendors_new"

def verify_sync():
    print("--- 🚀 Starting Review Sync Verification ---")
    
    # 1. Prepare Target Booking (Found previously for this user)
    # User ID: 699602e14888ea2688b84bed
    # Dummy Booking ID for testing: 69d07bf0da5956f365902dbd
    payload = {
        "userId": "699602e14888ea2688b84bed",
        "bookingId": "69d07bf0da5956f365902dbd",
        "serviceProviderId": "69932ac266da12767de69139",
        "rating": 5.0,
        "ratingDescription": "Excellent service! (Automated Verification Test)"
    }
    
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json"
    }

    print(f"📡 Sending Rating to Java API: {JAVA_API_URL}")
    try:
        response = requests.post(JAVA_API_URL, json=payload, headers=headers, timeout=10)
        print(f"✅ API Response Status: {response.status_code}")
        print(f"📝 API Response Body: {response.text}")
    except Exception as e:
        print(f"❌ Failed to reach Java API: {e}")
        print("--- ⚠️ Note: Java server must be running on localhost:8080 for this test ---")

    print("\n🔍 Checking MongoDB (doffair_vendors_new.reviews) for the record...")
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    # Wait a moment for sync
    time.sleep(2)
    
    # Search for the review in the secondary database
    # We search by bookingId (real one) and userId (review_by)
    query = {
        "booking_id": "69cff8076ef335228d0bd36a",
        "review_by": "699602e14888ea2688b84bed"
    }
    
    review = db.reviews.find_one(query, sort=[("created_at", -1)])
    
    if review:
        print("🌟 Verification SUCCESS! Review found in secondary database.")
        print(f"   Review ID: {review['_id']}")
        print(f"   Booking ID: {review.get('booking_id')}")
        print(f"   Rating: {review.get('rating')}")
        print(f"   Text: {review.get('review_text')}")
    else:
        print("❌ Verification FAILED: Review not found in secondary database.")
        print("   If API call failed above, this is expected.")

if __name__ == "__main__":
    verify_sync()
