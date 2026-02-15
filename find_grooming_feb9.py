import asyncio
import os
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

async def debug():
    from dotenv import load_dotenv
    load_dotenv()
    
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    # Grooming VID
    vid = "69522b6ce6a07c46de0f88d7"
    start = datetime(2026, 2, 9, 0, 0, 0)
    end = datetime(2026, 2, 9, 23, 59, 59)
    
    print(f"--- Bookings for Vertical {vid} (Grooming) on Feb 9th ---")
    cursor = db.bookings.find({
        "vertical_id": vid,
        "booking_date": {"$gte": start, "$lte": end}
    })
    
    async for doc in cursor:
        print(f"ID: {doc['_id']} | Date: {doc.get('booking_date')} | Status: {doc.get('status')} | Vendor: {doc.get('vendor_id')}")

if __name__ == "__main__":
    asyncio.run(debug())
