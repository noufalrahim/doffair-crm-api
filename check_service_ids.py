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
    
    ids = [ObjectId("69911bf89940cc1ef8081000"), ObjectId("69911c379940cc1ef8081002"), ObjectId("69914ab0a4f52a552db4fb41")]
    print(f"--- Checking Services ---")
    cursor = db.vendor_services.find({"_id": {"$in": ids}})
    async for doc in cursor:
        print(f"ID: {doc['_id']} | Name: {doc.get('name')} | VerticalID: {doc.get('vertical_id')}")

if __name__ == "__main__":
    asyncio.run(debug())
