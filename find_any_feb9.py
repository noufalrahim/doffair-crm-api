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
    
    # Feb 9th, 2026
    start = datetime(2026, 2, 9, 0, 0, 0)
    end = datetime(2026, 2, 9, 23, 59, 59)
    
    print(f"--- ANY Booking on Feb 9th, 2026 (Primary DB) ---")
    cursor = db_p["bookings"].find({
        "booking_date": {"$gte": start, "$lte": end}
    })
    
    found = False
    async for doc in cursor:
        found = True
        print(f"ID: {doc['_id']} | Date: {doc.get('booking_date')} | Status: {doc.get('status')} | Vendor: {doc.get('vendor_id')} | Vertical: {doc.get('vertical_id')} | IsOffline: {doc.get('is_offline')}")

    if not found:
        # Maybe booking_date is a string?
        print("Checking if booking_date is stored as string...")
        cursor_str = db_p["bookings"].find({
            "booking_date": {"$regex": "^2026-02-09"}
        })
        async for doc in cursor_str:
            found = True
            print(f"[STR] ID: {doc['_id']} | Date: {doc.get('booking_date')} | Status: {doc.get('status')} | Vendor: {doc.get('vendor_id')}")

    if not found:
        print("Still nothing. Searching by created_at in Feb 9th...")
        cursor_cr = db_p["bookings"].find({
            "created_at": {"$gte": start, "$lte": end}
        })
        async for doc in cursor_cr:
            found = True
            print(f"[CREATED] ID: {doc['_id']} | Date: {doc.get('booking_date')} | Created: {doc.get('created_at')} | Vendor: {doc.get('vendor_id')}")

    # Check Secondary DB too
    uri_secondary = os.getenv("MONGODB_URI_SECONDARY")
    db_name_secondary = os.getenv("MONGODB_DB_NAME_SECONDARY")
    client_s = AsyncIOMotorClient(uri_secondary)
    db_s = client_s[db_name_secondary]

    print(f"\n--- ANY Booking on Feb 9th, 2026 (Secondary DB) ---")
    cursor_s = db_s["bookings"].find({
        "startTime": {"$gte": start, "$lte": end}
    })
    async for doc in cursor_s:
        print(f"ID: {doc['_id']} | StartTime: {doc.get('startTime')} | Status: {doc.get('status')} | Vendor: {doc.get('serviceProviderId')}")

if __name__ == "__main__":
    asyncio.run(debug())
