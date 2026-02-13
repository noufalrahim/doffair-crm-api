
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv(".env")

MONGO_URL = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB_NAME")

async def migrate():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    collection = db["vendors"]
    
    print("🔄 Updating vendor status values...")
    
    # Update from SERVICE_TYPE_SELECTED to VERTICAL_SELECTED
    result = await collection.update_many(
        {"status": "SERVICE_TYPE_SELECTED"},
        {"$set": {"status": "VERTICAL_SELECTED"}}
    )
    
    print(f"✅ Successfully updated {result.modified_count} vendor documents.")
    print("🚀 Migration complete.")
    client.close()

if __name__ == "__main__":
    asyncio.run(migrate())
