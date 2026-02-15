import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def debug():
    from dotenv import load_dotenv
    load_dotenv()
    
    uri = os.getenv("MONGODB_URI_SECONDARY")
    db_name = os.getenv("MONGODB_DB_NAME_SECONDARY")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    # Check if 'bookings' collection is the right name in secondary
    print(f"--- All Bookings in {db_name} sorted by startTime ---")
    cursor = db.bookings.find({}).sort("startTime", -1).limit(50)
    
    async for d in cursor:
        print(f"ID: {d['_id']} | Start: {d.get('startTime')} | S: {d.get('status')} | V: {d.get('serviceProviderId')} | Type: {d.get('serviceProviderType')}")

if __name__ == "__main__":
    asyncio.run(debug())
