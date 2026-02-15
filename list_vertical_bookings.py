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
    
    vid = "69529fdb5a26a27c25c7c65a"
    
    print(f"--- All Bookings for Vertical {vid} (Primary DB) ---")
    cursor = db_p["bookings"].find({
        "vertical_id": vid
    })
    
    found = False
    async for doc in cursor:
        found = True
        print(f"ID: {doc['_id']} | Date: {doc.get('booking_date')} | Status: {doc.get('status')} | Vendor: {doc.get('vendor_id')} | Name: {doc.get('user_name')}")

    if not found:
        print("No bookings found for this vertical in Primary DB.")

    # Check Secondary DB by codes
    uri_secondary = os.getenv("MONGODB_URI_SECONDARY")
    db_name_secondary = os.getenv("MONGODB_DB_NAME_SECONDARY")
    client_s = AsyncIOMotorClient(uri_secondary)
    db_s = client_s[db_name_secondary]
    
    vertical = await db_p["verticals"].find_one({"_id": ObjectId(vid)})
    codes = vertical.get('code', []) if vertical else []
    
    print(f"\n--- All Bookings for Codes {codes} (Secondary DB) ---")
    cursor_s = db_s["bookings"].find({
        "serviceProviderType": {"$in": codes}
    })
    
    found_s = False
    async for doc in cursor_s:
        found_s = True
        print(f"ID: {doc['_id']} | StartTime: {doc.get('startTime')} | Status: {doc.get('status')} | Vendor: {doc.get('serviceProviderId')}")
    
    if not found_s:
        print("No bookings found for these codes in Secondary DB.")

if __name__ == "__main__":
    asyncio.run(debug())
