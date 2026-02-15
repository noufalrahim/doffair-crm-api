import asyncio
import os
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

async def debug():
    from dotenv import load_dotenv
    load_dotenv()
    
    uri_secondary = os.getenv("MONGODB_URI_SECONDARY")
    db_name_secondary = os.getenv("MONGODB_DB_NAME_SECONDARY")
    client_s = AsyncIOMotorClient(uri_secondary)
    db_s = client_s[db_name_secondary]
    
    vendor_id = "69905d49c857901ed124f37b"
    # Whole month of Feb 2026
    start = datetime(2026, 2, 1)
    end = datetime(2026, 2, 28, 23, 59, 59)
    
    print(f"--- All Bookings for Vendor {vendor_id} in Feb 2026 (Secondary DB) ---")
    cursor_s = db_s["bookings"].find({
        "$or": [
            {"serviceProviderId": ObjectId(vendor_id)},
            {"serviceProviderId": vendor_id}
        ]
    }).sort("startTime", -1)
    
    found = False
    async for doc in cursor_s:
        st = doc.get("startTime")
        if st and start <= st <= end:
            found = True
            print(f"ID: {doc['_id']} | StartTime: {st} | Type: {doc.get('serviceProviderType')} | Status: {doc.get('status')}")
    
    if not found:
        print("No bookings found in Feb 2026 for this vendor.")

if __name__ == "__main__":
    asyncio.run(debug())
