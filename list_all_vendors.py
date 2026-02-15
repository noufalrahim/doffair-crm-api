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
    
    print(f"--- All Vendors in {db_name} ---")
    cursor = db.vendors.find({}).limit(20)
    async for doc in cursor:
        print(f"ID: {doc['_id']} | DisplayName: {doc.get('display_name')} | BusinessName: {doc.get('business_name')} | Email: {doc.get('email')} | Phone: {doc.get('phone')}")

if __name__ == "__main__":
    asyncio.run(debug())
