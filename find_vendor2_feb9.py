import asyncio
import os
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

async def debug():
    from dotenv import load_dotenv
    load_dotenv()
    
    uri_primary = os.getenv("MONGODB_URI")
    db_name_primary = os.getenv("MONGODB_DB_NAME")
    client_p = AsyncIOMotorClient(uri_primary)
    db_p = client_p[db_name_primary]
    
    vendor_id = "699149baa4f52a552db4fb3c"
    start = datetime(2026, 2, 9, 0, 0, 0)
    end = datetime(2026, 2, 9, 23, 59, 59)
    
    print(f"--- Bookings for Vendor {vendor_id} on Feb 9th (Primary DB) ---")
    cursor = db_p["bookings"].find({
        "vendor_id": vendor_id,
        "booking_date": {"$gte": start, "$lte": end}
    })
    
    async for doc in cursor:
        print(f"ID: {doc['_id']} | Date: {doc.get('booking_date')} | Vertical: {doc.get('vertical_id')} | Status: {doc.get('status')}")

    uri_secondary = os.getenv("MONGODB_URI_SECONDARY")
    db_name_secondary = os.getenv("MONGODB_DB_NAME_SECONDARY")
    client_s = AsyncIOMotorClient(uri_secondary)
    db_s = client_s[db_name_secondary]
    
    print(f"\n--- Bookings for Vendor {vendor_id} on Feb 9th (Secondary DB) ---")
    cursor_s = db_s["bookings"].find({
        "$or": [
            {"serviceProviderId": ObjectId(vendor_id)},
            {"serviceProviderId": vendor_id}
        ],
        "startTime": {"$gte": start, "$lte": end}
    })
    async for doc in cursor_s:
        print(f"ID: {doc['_id']} | StartTime: {doc.get('startTime')} | Type: {doc.get('serviceProviderType')} | Status: {doc.get('status')}")

if __name__ == "__main__":
    asyncio.run(debug())
