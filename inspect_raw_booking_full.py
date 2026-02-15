import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

async def inspect():
    from dotenv import load_dotenv
    load_dotenv()
    
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    bid = "6991507bb67d2e018f6cfe07"
    print(f"--- Raw Booking {bid} ---")
    doc = await db.bookings.find_one({"_id": ObjectId(bid)})
    import pprint
    pprint.pprint(doc)

if __name__ == "__main__":
    asyncio.run(inspect())
