
import asyncio
from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys

# Add current directory to path so we can import internal modules
sys.path.append(os.getcwd())

from core.database import get_engine
from admin.models.vertical import Vertical

METADATA = {
    "grooming": {"url": "/groom/overview", "icon": "/services/groom.png", "priority": 1},
    "vet": {"url": "/vet/overview", "icon": "/services/vet.png", "priority": 0},
    "boarding": {"url": "/boarding/overview", "icon": "/services/boarding.png", "priority": 2},
    "petcafe": {"url": "/petcafe/overview", "icon": "/services/shop.png", "priority": 3},
    "pet_cafe": {"url": "/petcafe/overview", "icon": "/services/shop.png", "priority": 3},
}

async def initialize():
    engine = get_engine()
    
    print("Fetching verticals...")
    verticals = await engine.find(Vertical)
    
    for st in verticals:
        updated = False
        for code in st.code:
            if code in METADATA:
                meta = METADATA[code]
                st.url = meta["url"]
                st.icon = meta["icon"]
                st.priority = meta["priority"]
                updated = True
                print(f"Updating {st.display_name} ({code}) with metadata.")
                break
        
        if updated:
            await engine.save(st)
        else:
            print(f"No metadata found for {st.display_name} (codes: {st.code})")

    print("Initialization complete.")

if __name__ == "__main__":
    asyncio.run(initialize())
