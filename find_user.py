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
    
    print(f"--- Searching for User 'Noufal' ---")
    cursor = db.users.find({
        "$or": [
            {"username": {"$regex": "noufal", "$options": "i"}},
            {"firstName": {"$regex": "noufal", "$options": "i"}},
            {"phone": {"$regex": "9190", "$options": "i"}} # Just an example phone prefix
        ]
    })
    
    async for doc in cursor:
        print(f"ID: {doc['_id']} | Name: {doc.get('firstName')} | Phone: {doc.get('phone')} | Role: {doc.get('role')}")

if __name__ == "__main__":
    asyncio.run(debug())
