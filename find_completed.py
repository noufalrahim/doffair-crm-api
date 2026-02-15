import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def debug():
    from dotenv import load_dotenv
    load_dotenv()
    
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    print(f"--- Completed Bookings ({db_name}) ---")
    docs = await db.bookings.find({"status": "completed"}).limit(10).to_list(length=10)
    for d in docs:
        print(f"ID: {d['_id']} | Date: {d.get('booking_date')} | Vendor: {d.get('vendor_id')} | Vertical: {d.get('vertical_id')}")

    uri_s = os.getenv("MONGODB_URI_SECONDARY")
    db_name_s = os.getenv("MONGODB_DB_NAME_SECONDARY")
    client_s = AsyncIOMotorClient(uri_s)
    db_s = client_s[db_name_s]
    
    print(f"\n--- Completed Bookings ({db_name_s}) ---")
    docs_s = await db_s.bookings.find({"status": "completed"}).limit(5).to_list(length=5)
    for d in docs_s:
        print(f"ID: {d['_id']} | StartTime: {d.get('startTime')} | Vendor: {d.get('serviceProviderId')} | Type: {d.get('serviceProviderType')}")

if __name__ == "__main__":
    asyncio.run(debug())
