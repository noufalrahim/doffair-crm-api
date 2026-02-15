import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

async def debug():
    from dotenv import load_dotenv
    load_dotenv()
    
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    vendor_id = "69905d49c857901ed124f37b"
    print(f"--- Checking vendor_verticals mapping for Vendor {vendor_id} ---")
    cursor = db.vendor_verticals.find({"vendor_id": vendor_id})
    async for doc in cursor:
        vid = doc.get("vertical_id")
        v_doc = await db.verticals.find_one({"_id": ObjectId(vid)}) if vid else None
        print(f"VerticalID: {vid} | Name: {v_doc.get('display_name') if v_doc else 'Unknown'}")

if __name__ == "__main__":
    asyncio.run(debug())
