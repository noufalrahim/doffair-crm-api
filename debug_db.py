
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def check_data():
    uri = "mongodb+srv://doffair_dev:yTwgZQf2t3XiSXos@development-cluster.9w53x.mongodb.net/?retryWrites=true&w=majority&appName=development-cluster"
    client = AsyncIOMotorClient(uri)
    db = client["doffair_vendors_new"]
    
    target_date_str = "2026-02-20"
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    midnight = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    print(f"Checking for date: {target_date_str}")
    
    # 1. Check for Holidays
    holidays = await db["holidays"].find({
        "date": {"$gte": midnight, "$lte": end_of_day}
    }).to_list(length=10)
    
    print(f"\nHolidays found: {len(holidays)}")
    for h in holidays:
        print(f" - {h.get('name')} (All day: {h.get('is_all_day')})")

    # 2. Check for Weekly Availability (day_of_week = 4 for Friday)
    day_of_week = 4
    availabilities = await db["availability"].find({
        "day_of_week": day_of_week
    }).to_list(length=50)
    
    print(f"\nWeekly Availabilities for Day {day_of_week} Found: {len(availabilities)}")
    # Just list some to see the structure and vendor/location
    for a in availabilities[:10]:
         print(f" - Vendor: {a.get('vendor_id')}, Loc: {a.get('location_id')}, Vert: {a.get('vertical_id')}, Time: {a.get('start_time')} - {a.get('end_time')}")

    client.close()

if __name__ == "__main__":
    asyncio.run(check_data())
