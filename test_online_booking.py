import asyncio
from core.database import get_secondary_motor_client
from core.config import settings

async def main():
    try:
        sec_client = get_secondary_motor_client()
        sec_db = sec_client[settings.MONGODB_DB_NAME_SECONDARY]
        
        online = await sec_db.bookings.find_one({})
        print("\n--- SECONDARY ONLINE BOOKING KEYS ---")
        if online:
            for k, v in online.items():
                print(f"{k}: {type(v).__name__}")
                if k in ["userName", "serviceProviderName", "serviceId", "serviceName", "startTime", "price", "status"]:
                    print(f"  -> {k} = {v}")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
