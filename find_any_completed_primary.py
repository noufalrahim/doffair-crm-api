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
    
    print(f"--- Searching for ANY Completed Booking in {db_name} ---")
    cursor = db.bookings.find({"status": "completed"})
    
    count = 0
    async for doc in cursor:
        count += 1
        print(f"[{count}] ID: {doc['_id']} | Date: {doc.get('booking_date')} | Vendor: {doc.get('vendor_id')} | Vertical: {doc.get('vertical_id')}")
    
    if count == 0:
        print("No completed bookings found in Primary DB!")

if __name__ == "__main__":
    asyncio.run(debug())
