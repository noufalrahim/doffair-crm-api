import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

async def debug():
    from dotenv import load_dotenv
    load_dotenv()
    
    uri = os.getenv("MONGODB_URI_SECONDARY")
    db_name = os.getenv("MONGODB_DB_NAME_SECONDARY")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    vid = "69529fdb5a26a27c25c7c65a"
    print(f"--- Checking Vertical {vid} in {db_name} ---")
    doc = await db.verticals.find_one({"_id": ObjectId(vid)})
    if doc:
        print(f"Vertical found: {doc.get('display_name')}")
    else:
        print("Vertical not found!")

if __name__ == "__main__":
    asyncio.run(debug())
