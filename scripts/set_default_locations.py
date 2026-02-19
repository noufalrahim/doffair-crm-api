"""
Migration script: Set first location of every vendor as is_default=True.
Targets ONLY the doffair_vendors_new database.

Usage:
    python scripts/set_default_locations.py
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = "doffair_vendors_new"  # Hardcoded to ensure correct target


async def migrate():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    collection = db["vendor_locations"]

    print(f"Connected to database: {DB_NAME}")
    print(f"Collection: vendor_locations")

    # Get all distinct vendor_ids
    vendor_ids = await collection.distinct("vendor_id")
    print(f"Found {len(vendor_ids)} vendors with locations")

    updated_count = 0
    skipped_count = 0

    for vendor_id in vendor_ids:
        # Check if any location already has is_default=True
        existing_default = await collection.find_one(
            {"vendor_id": vendor_id, "is_default": True}
        )

        if existing_default:
            skipped_count += 1
            continue

        # Find the first location (by created_at, oldest first)
        first_location = await collection.find_one(
            {"vendor_id": vendor_id},
            sort=[("created_at", 1)],
        )

        if first_location:
            # Set all locations for this vendor to is_default=False first
            await collection.update_many(
                {"vendor_id": vendor_id},
                {"$set": {"is_default": False}},
            )

            # Set the first location as default
            await collection.update_one(
                {"_id": first_location["_id"]},
                {"$set": {"is_default": True}},
            )
            updated_count += 1
            print(f"  ✅ Vendor {vendor_id}: set location {first_location['_id']} as default")

    print(f"\nDone!")
    print(f"  Updated: {updated_count} vendors")
    print(f"  Skipped (already had default): {skipped_count}")

    client.close()


if __name__ == "__main__":
    asyncio.run(migrate())
