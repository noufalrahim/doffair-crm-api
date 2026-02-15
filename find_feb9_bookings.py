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
    
    print(f"--- Bookings on Feb 9th, 2026 (Primary DB) ---")
    cursor = db_p["bookings"].find({
        "booking_date": {"$gte": start, "$lte": end}
    })
    
    found = False
    async for doc in cursor:
        found = True
        print(f"ID: {doc['_id']} | Date: {doc.get('booking_date')} | Status: {doc.get('status')} | Vertical: {doc.get('vertical_id')} | Vendor: {doc.get('vendor_id')} | Name: {doc.get('user_name')}")

    if not found:
        print("No bookings found on Feb 9th.")

    # Check Secondary DB too
    uri_secondary = os.getenv("MONGODB_URI_SECONDARY")
    db_name_secondary = os.getenv("MONGODB_DB_NAME_SECONDARY")
    client_s = AsyncIOMotorClient(uri_secondary)
    db_s = client_s[db_name_secondary]
    
    print(f"\n--- Bookings on Feb 9th, 2026 (Secondary DB) ---")
    cursor_s = db_s["bookings"].find({
        "startTime": {"$gte": start, "$lte": end}
    })
    
    found_s = False
    async for doc in cursor_s:
        found_s = True
        print(f"ID: {doc['_id']} | StartTime: {doc.get('startTime')} | Status: {doc.get('status')} | Vendor: {doc.get('serviceProviderId')} | Type: {doc.get('serviceProviderType')}")
    
    if not found_s:
        print("No bookings found on Feb 9th in Secondary DB.")

if __name__ == "__main__":
    asyncio.run(debug())
