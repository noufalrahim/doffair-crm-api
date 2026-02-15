import asyncio
import os
from datetime import datetime, timedelta
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

async def debug():
    from dotenv import load_dotenv
    load_dotenv()
    
    uri_primary = os.getenv("MONGODB_URI")
    db_name_primary = os.getenv("MONGODB_DB_NAME")
    client_p = AsyncIOMotorClient(uri_primary)
    db_p = client_p[db_name_primary]
    
    # Last 30 days
    recent = datetime.now() - timedelta(days=30)
    
    print(f"--- All Bookings in Last 30 Days (Primary DB) ---")
    cursor = db_p["bookings"].find({
        # "booking_date": {"$gte": recent} # Removing date filter to see EVERYTHING first
    }).sort("created_at", -1).limit(50)
    
    async for doc in cursor:
        print(f"ID: {doc['_id']} | Date: {doc.get('booking_date')} | Created: {doc.get('created_at')} | Status: {doc.get('status')} | Vertical: {doc.get('vertical_id')} | Vendor: {doc.get('vendor_id')}")

if __name__ == "__main__":
    asyncio.run(debug())
