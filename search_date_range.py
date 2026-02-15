import asyncio
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

async def search_range():
    from dotenv import load_dotenv
    load_dotenv()
    
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    # 2026-02-20T18:30:00.000Z to 2026-02-26T18:30:00.000Z
    start = datetime.fromisoformat("2026-02-20T18:30:00+00:00").replace(tzinfo=None)
    end = datetime.fromisoformat("2026-02-26T18:30:00+00:00").replace(tzinfo=None)
    
    print(f"--- Bookings in ({db_name}) Range: {start} to {end} ---")
    query = {"booking_date": {"$gte": start, "$lte": end}}
    # query = {"status": "confirmed"} # Optional: relax to see anything
    
    cursor = db.bookings.find(query)
    async for d in cursor:
        print(f"ID: {d['_id']} | Date: {d.get('booking_date')} | S: {d.get('status')} | V: {d.get('vendor_id')} | U: {d.get('user_name')}")

if __name__ == "__main__":
    asyncio.run(search_range())
