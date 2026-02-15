import asyncio
import os
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

async def debug():
    from dotenv import load_dotenv
    load_dotenv()
    
    uri = os.getenv("MONGODB_URI_SECONDARY")
    db_name = os.getenv("MONGODB_DB_NAME_SECONDARY")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    start = datetime(2026, 2, 9, 0, 0, 0)
    end = datetime(2026, 2, 9, 23, 59, 59)
    
    print(f"--- ANY Booking on Feb 9th, 2026 in {db_name} (Secondary) ---")
    cursor = db.bookings.find({
        "startTime": {"$gte": start, "$lte": end}
    })
    
    count = 0
    async for doc in cursor:
        count += 1
        print(f"[{count}] ID: {doc['_id']} | Start: {doc.get('startTime')} | Vendor: {doc.get('serviceProviderId')} | Type: {doc.get('serviceProviderType')} | Status: {doc.get('status')}")

    if count == 0:
        print("No bookings found on Feb 9th in Secondary DB.")

if __name__ == "__main__":
    asyncio.run(debug())
