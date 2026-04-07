#!/usr/bin/env python3
"""
Script to check what vendor IDs exist in the database
"""

import asyncio
from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient
from vendor.models.doctor_availability import Availability
from core.config import settings

async def check_vendor_ids():
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    engine = AIOEngine(client=client, database=settings.MONGODB_DB_NAME)
    
    # Get all availability records to see what vendor IDs exist
    all_records = await engine.find(Availability)
    
    print(f"Total availability records in database: {len(all_records)}")
    
    vendor_ids = set()
    for record in all_records:
        vendor_ids.add(record.vendor_id)
    
    print(f"Vendor IDs found: {list(vendor_ids)}")
    
    # Check records for our specific location
    location_id = "69d4a9ae398b987f392c1631"
    location_records = await engine.find(Availability, Availability.location_id == location_id)
    
    print(f"\nRecords for location {location_id}:")
    for record in location_records:
        print(f"  - Vendor: {record.vendor_id}, Vertical: {record.vertical_id}, Day {record.day_of_week}: {record.start_time}-{record.end_time}")
    
    # Let's also check what vendor IDs are used for this vertical
    vertical_id = "69522b6ce6a07c46de0f88d7"
    vertical_records = await engine.find(Availability, Availability.vertical_id == vertical_id)
    
    print(f"\nRecords for vertical {vertical_id}:")
    for record in vertical_records:
        print(f"  - Vendor: {record.vendor_id}, Location: {record.location_id}, Day {record.day_of_week}: {record.start_time}-{record.end_time}")

if __name__ == "__main__":
    asyncio.run(check_vendor_ids())
