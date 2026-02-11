
import asyncio
from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(".env")

MONGO_URL_SECONDARY = os.getenv("MONGODB_URI_SECONDARY")
DB_NAME_SECONDARY = os.getenv("MONGODB_DB_NAME_SECONDARY")

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        from bson import DBRef
        if isinstance(obj, DBRef):
            return {"$ref": obj.collection, "$id": str(obj.id), "$db": obj.database}
        return super().default(obj)

async def inspect():
    client = AsyncIOMotorClient(MONGO_URL_SECONDARY)
    db = client[DB_NAME_SECONDARY]
    collection = db["bookings"]
    
    # vendor_id = "69881a54d1bbd0a7b3f6d2bf"
    
    # Just find ONE booking for this vendor to see its structure
    print("--- Inspecting Secondary DB Bookings ---")
    docs = await collection.find({}).limit(5).to_list(length=5)
    
    for i, doc in enumerate(docs):
        print(f"\n--- Document {i+1} ---")
        print(json.dumps(doc, indent=2, cls=JSONEncoder))

if __name__ == "__main__":
    asyncio.run(inspect())
