import asyncio
import os
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

async def debug():
    from dotenv import load_dotenv
    load_dotenv()
    
    uri_primary = os.getenv("MONGODB_URI")
    db_name_primary = os.getenv("MONGODB_DB_NAME")
    client_p = AsyncIOMotorClient(uri_primary)
    db_p = client_p[db_name_primary]
    
    print(f"--- Finding Vendors ---")
    cursor = db_p["vendors"].find({}).limit(10)
    async for doc in cursor:
        print(f"ID: {doc['_id']} | Name: {doc.get('name')} | DisplayName: {doc.get('display_name')} | Phone: {doc.get('phone')}")

if __name__ == "__main__":
    asyncio.run(debug())
