
import asyncio
import sys
from pathlib import Path
from bson import ObjectId

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings

async def main():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB_NAME]
    
    vertical_ids = ["69522b6ce6a07c46de0f88d7", "69529fdb5a26a27c25c7c65a"]
    
    print("--- Inspecting Verticals ---")
    collection = db["verticals"]
    
    for v_id in vertical_ids:
        v = await collection.find_one({"_id": ObjectId(v_id)})
        if v:
            print(f"ID: {v_id}, Name: {v.get('display_name')}, Code: {v.get('code')}")
        else:
            print(f"ID: {v_id} NOT FOUND in verticals collection")

    client.close()

if __name__ == "__main__":
    asyncio.run(main())
