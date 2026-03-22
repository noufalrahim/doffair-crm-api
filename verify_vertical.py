import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def check():
    load_dotenv()
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    vertical_id = "69b564ef7c13f839ae78e0ba"
    doc = await db.verticals.find_one({"_id": vertical_id})
    if not doc:
        try:
            from bson import ObjectId
            doc = await db.verticals.find_one({"_id": ObjectId(vertical_id)})
        except:
            pass
    
    print(f"Vertical Doc: {doc}")

if __name__ == "__main__":
    asyncio.run(check())
