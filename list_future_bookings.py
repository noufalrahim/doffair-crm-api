import asyncio
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

async def list_future():
    from dotenv import load_dotenv
    load_dotenv()
    
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    now = datetime(2026, 2, 15)
    print(f"--- Future Bookings in Primary ({db_name}) from {now} ---")
    cursor = db.bookings.find({"booking_date": {"$gte": now}}).sort("booking_date", 1)
    
    async for d in cursor:
        print(f"ID: {d['_id']} | Date: {d.get('booking_date')} | S: {d.get('status')} | V: {d.get('vendor_id')} | U: {d.get('user_name')} | SName: {d.get('service_name')}")

if __name__ == "__main__":
    asyncio.run(list_future())
