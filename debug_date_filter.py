import asyncio
import os
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

async def debug():
    # Load env manually as if running from shell
    from dotenv import load_dotenv
    load_dotenv()
    
    uri_primary = os.getenv("MONGODB_URI")
    db_name_primary = os.getenv("MONGODB_DB_NAME")
    uri_secondary = os.getenv("MONGODB_URI_SECONDARY")
    db_name_secondary = os.getenv("MONGODB_DB_NAME_SECONDARY")
    
    client_p = AsyncIOMotorClient(uri_primary)
    db_p = client_p[db_name_primary]
    
    client_s = AsyncIOMotorClient(uri_secondary)
    db_s = client_s[db_name_secondary]
    
    vid = "69529fdb5a26a27c25c7c65a"
    start = datetime(2026, 2, 3, 18, 30)
    end = datetime(2026, 3, 10, 18, 30)
    
    print(f"--- Vertical Info ---")
    vertical = await db_p["verticals"].find_one({"_id": ObjectId(vid)})
    if vertical:
        print(f"Vertical: {vertical.get('display_name')} (Codes: {vertical.get('code')})")
        codes = vertical.get('code', [])
    else:
        print("Vertical not found!")
        return

    print(f"\n--- Searching Primary DB (Modern/Offline) ---")
    # Search all bookings for this vertical in the date range
    cursor = db_p["bookings"].find({
        "vertical_id": vid,
        "booking_date": {"$gte": start, "$lte": end}
    })
    
    count = 0
    async for doc in cursor:
        count += 1
        print(f"[{count}] ID: {doc['_id']} | Date: {doc.get('booking_date')} | Status: {doc.get('status')} | Vendor: {doc.get('vendor_id')} | Offline: {doc.get('is_offline')}")

    print(f"\n--- Searching Secondary DB (Legacy) ---")
    cursor_s = db_s["bookings"].find({
        "serviceProviderType": {"$in": codes},
        "startTime": {"$gte": start, "$lte": end}
    })
    
    count_s = 0
    async for doc in cursor_s:
        count_s += 1
        print(f"[{count_s}] ID: {doc['_id']} | StartTime: {doc.get('startTime')} | Status: {doc.get('status')} | Vendor: {doc.get('serviceProviderId')}")

if __name__ == "__main__":
    asyncio.run(debug())
