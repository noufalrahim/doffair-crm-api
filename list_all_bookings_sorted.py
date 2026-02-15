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
    
    print(f"--- All Bookings in {db_name} sorted by booking_date ---")
    cursor = db.bookings.find({}).sort("booking_date", -1).limit(50)
    
    async for d in cursor:
        print(f"ID: {d['_id']} | Date: {d.get('booking_date')} | S: {d.get('status')} | V: {d.get('vendor_id')} | VID: {d.get('vertical_id')}")

if __name__ == "__main__":
    asyncio.run(debug())
