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
    
    print(f"--- Booking Service/Vertical Names ({db_name}) ---")
    docs = await db.bookings.find().sort("created_at", -1).limit(10).to_list(length=10)
    for d in docs:
        print(f"ID: {d['_id']} | SName: {d.get('service_name')} | VName: {d.get('vertical_name')} | VID: {d.get('vertical_id')}")

if __name__ == "__main__":
    asyncio.run(debug())
