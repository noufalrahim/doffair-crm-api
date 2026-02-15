import asyncio
import os
from datetime import datetime
from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient
from user.services.booking_service import get_vendor_bookings

async def verify():
    from dotenv import load_dotenv
    load_dotenv()
    
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME")
    client = AsyncIOMotorClient(uri)
    engine = AIOEngine(client=client, database=db_name)
    
    vendor_id = "69905d49c857901ed124f37b"
    vet_vid = "69529fdb5a26a27c25c7c65a"
    
    print(f"--- Verifying fix for Vendor {vendor_id} and Vertical {vet_vid} ---")
    
    # 1. Test Service Layer
    docs, total = await get_vendor_bookings(
        engine, vendor_id, vertical_id=vet_vid, limit=10
    )
    
    print(f"Total bookings found in service layer: {total}")
    for b, p in docs:
        print(f"ID: {b['id']} | VID: {b.get('vertical_id')} | VName: {b.get('vertical_name')} | Date: {b.get('booking_date')}")

    # 2. Check explicitly for the previously missing booking
    target_id = "6991507bb67d2e018f6cfe07"
    found = any(b['id'] == target_id for b, p in docs)
    if found:
        print(f"SUCCESS: Previously missing booking {target_id} (with null VID) is now FOUND!")
    else:
        print(f"FAILURE: Booking {target_id} still not found in filtered results.")

if __name__ == "__main__":
    asyncio.run(verify())
