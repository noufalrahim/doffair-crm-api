import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def verify():
    load_dotenv()
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    
    col = db['medications']
    
    count = await col.count_documents({})
    print(f"Total medications in collection: {count}")
    
    vendors = ["69947d80f7f198a8f13efebf", "69905d49c857901ed124f37b"]
    for vid in vendors:
        vcount = await col.count_documents({"vendor_id": vid})
        print(f"Vendor {vid}: {vcount} medicines")
        
        # Sample one
        doc = await col.find_one({"vendor_id": vid})
        if doc:
            print(f" - Sample: {doc.get('name')} ({doc.get('category')})")

if __name__ == "__main__":
    asyncio.run(verify())
