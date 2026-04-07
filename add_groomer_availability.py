#!/usr/bin/env python3
"""
Script to add test availability data for grooming
"""

import asyncio
from datetime import datetime
from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient
from vendor.models.doctor_availability import Availability
from core.config import settings

async def add_test_availability():
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    engine = AIOEngine(client=client, database=settings.MONGODB_DB_NAME)
    
    # Test availability data for grooming (Monday 9 AM - 5 PM)
    # Using the actual locationId and verticalId from the debug logs
    location_id = "69d4a9ae398b987f392c1631"
    vertical_id = "69522b6ce6a07c46de0f88d7"
    
    # Based on the database analysis, the correct vendor ID for this location is:
    vendor_id = "69d4a95b398b987f392c162b"
    print(f"Using vendor ID based on location analysis: {vendor_id}")
    
    # First, let's check what vendor IDs exist for this location/vertical
    existing_records = await engine.find(Availability, 
        Availability.location_id == location_id,
        Availability.vertical_id == vertical_id
    )
    
    print(f"Found {len(existing_records)} existing availability records for this location/vertical:")
    for record in existing_records:
        print(f"  - Vendor ID: {record.vendor_id}, Day: {record.day_of_week}, Hours: {record.start_time}-{record.end_time}")
    
    if existing_records:
        # Delete existing records to avoid duplicates
        print("Deleting existing records...")
        for record in existing_records:
            await engine.delete(record)
    
    test_availabilities = [
        Availability(
            vendor_id=vendor_id,
            vertical_id=vertical_id,
            location_id=location_id,
            day_of_week=0,  # Monday
            start_time="09:00",
            end_time="17:00"
        ),
        Availability(
            vendor_id=vendor_id,
            vertical_id=vertical_id,
            location_id=location_id,
            day_of_week=1,  # Tuesday
            start_time="09:00",
            end_time="17:00"
        ),
        Availability(
            vendor_id=vendor_id,
            vertical_id=vertical_id,
            location_id=location_id,
            day_of_week=2,  # Wednesday
            start_time="09:00",
            end_time="17:00"
        ),
        Availability(
            vendor_id=vendor_id,
            vertical_id=vertical_id,
            location_id=location_id,
            day_of_week=3,  # Thursday
            start_time="09:00",
            end_time="17:00"
        ),
        Availability(
            vendor_id=vendor_id,
            vertical_id=vertical_id,
            location_id=location_id,
            day_of_week=4,  # Friday
            start_time="09:00",
            end_time="17:00"
        ),
        Availability(
            vendor_id=vendor_id,
            vertical_id=vertical_id,
            location_id=location_id,
            day_of_week=5,  # Saturday
            start_time="09:00",
            end_time="17:00"
        ),
        Availability(
            vendor_id=vendor_id,
            vertical_id=vertical_id,
            location_id=location_id,
            day_of_week=6,  # Sunday
            start_time="09:00",
            end_time="17:00"
        )
    ]
    
    # Save to database
    for availability in test_availabilities:
        await engine.save(availability)
        print(f"Added availability for day {availability.day_of_week}: {availability.start_time} - {availability.end_time}")
    
    print("Test availability data added successfully!")
    print(f"Location ID: {location_id}")
    print(f"Vertical ID: {vertical_id}")
    print(f"Vendor ID: {vendor_id}")

if __name__ == "__main__":
    asyncio.run(add_test_availability())
