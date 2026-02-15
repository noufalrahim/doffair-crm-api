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
    
    print(f"--- Raw Bookings Inspection ({db_name}) ---")
    docs = await db.bookings.find().sort("created_at", -1).limit(5).to_list(length=5)
    for d in docs:
        b_date = d.get("booking_date")
        print(f"ID: {d['_id']} | Date: {b_date} | DateType: {type(b_date)} | Status: {d.get('status')} | Vendor: {d.get('vendor_id')}")

if __name__ == "__main__":
    asyncio.run(debug())
