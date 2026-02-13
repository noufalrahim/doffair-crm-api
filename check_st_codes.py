
import asyncio
from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
from dotenv import load_dotenv

load_dotenv(".env")

# Import models
from admin.models.vertical import Vertical

# Mongo config
MONGO_URL = os.getenv("MONGODB_URI") 
DB_NAME = os.getenv("MONGODB_DB_NAME")

async def check_codes():
    client = AsyncIOMotorClient(MONGO_URL)
    engine = AIOEngine(client=client, database=DB_NAME)
    
    st_id = "69522b6ce6a07c46de0f88d7"
    st = await engine.find_one(Vertical, Vertical.id == ObjectId(st_id))
    
    if st:
        print(f"Vertical: {st.display_name}")
        print(f"Codes: {st.code}")
    else:
        print(f"Vertical {st_id} not found!")

if __name__ == "__main__":
    asyncio.run(check_codes())
