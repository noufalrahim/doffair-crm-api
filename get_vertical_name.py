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
    
    vid = "69522b6ce6a07c46de0f88d7"
    print(f"--- Checking Vertical {vid} ---")
    doc = await db.verticals.find_one({"_id": ObjectId(vid)})
    if doc:
        print(f"Vertical: {doc.get('display_name')} | InternalName: {doc.get('name')}")
    else:
        print("Vertical not found!")

if __name__ == "__main__":
    asyncio.run(debug())
