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
    status_filter = "confirmed"
    search = "geq"
    start_date = datetime.fromisoformat("2026-02-20T18:30:00.000+00:00")
    end_date = datetime.fromisoformat("2026-02-26T18:30:00.000+00:00")
    
    print(f"--- Verifying /bookings/vendor/my-bookings Filters ---")
    print(f"Vendor: {vendor_id} | Status: {status_filter} | Search: {search}")
    print(f"Range: {start_date} to {end_date}")
    
    # Test Service Layer (which the router now calls with these params)
    docs, total = await get_vendor_bookings(
        engine, 
        vendor_id, 
        status_filter=status_filter, 
        search=search,
        start_date=start_date,
        end_date=end_date,
        is_offline=True, # This endpoint is hardcoded to is_offline=True
        limit=10
    )
    
    print(f"Total bookings found: {total}")
    for b, p in docs:
        print(f"ID: {b['id']} | Status: {b['status']} | SName: {b['service_name']} | Date: {b['booking_date']}")

    # Check for the specific geq booking if it exists in the provided range
    # The user mentioned search=geq, so I expect to see bookings with "geq" in names/notes
    # Based on previous list, ID 6991507bb67d2e018f6cfe07 date is 2026-02-20 06:30:00
    # The range provided 2026-02-20T18:30:00 UTC might EXCLUDE it if it's early morning.
    # Let's see.

if __name__ == "__main__":
    asyncio.run(verify())
