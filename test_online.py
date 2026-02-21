import asyncio
import os
from dotenv import load_dotenv
from core.database import get_secondary_motor_client
from core.config import settings

async def main():
    load_dotenv()
    sec_client = get_secondary_motor_client()
    db = sec_client[settings.MONGODB_DB_NAME_SECONDARY]
    
    doc = await db.bookings.find_one()
    if not doc:
        print("NO DOC FOUND")
        return
        
    print('--- Keys ---')
    print(list(doc.keys()))
    if 'services' in doc and doc['services']:
        print('--- First Service ---')
        print(doc['services'][0])

if __name__ == "__main__":
    asyncio.run(main())
