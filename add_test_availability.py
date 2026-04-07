#!/usr/bin/env python3
"""
Script to add test availability data for grooming
"""

import asyncio
from datetime import datetime
from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient
from vendor.models.doctor_availability import Availability
from core.config import MONGODB_URL

async def add_test_availability():
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    engine = AIOEngine(motor_client=client, database="doffair")
    
    # Test availability data for grooming (Monday 9 AM - 5 PM)
    test_availabilities = [
        Availability(
            vendor_id="test_vendor_id",  # Replace with actual vendor ID
            vertical_id="test_vertical_id",  # Replace with actual vertical ID  
            location_id="test_location_id",  # Replace with actual location ID
            day_of_week=0,  # Monday
            start_time="09:00",
            end_time="17:00"
        ),
        Availability(
            vendor_id="test_vendor_id",
            vertical_id="test_vertical_id",
            location_id="test_location_id", 
            day_of_week=1,  # Tuesday
            start_time="09:00",
            end_time="17:00"
        ),
        Availability(
            vendor_id="test_vendor_id",
            vertical_id="test_vertical_id",
            location_id="test_location_id",
            day_of_week=2,  # Wednesday
            start_time="09:00",
            end_time="17:00"
        ),
        Availability(
            vendor_id="test_vendor_id",
            vertical_id="test_vertical_id",
            location_id="test_location_id",
            day_of_week=3,  # Thursday
            start_time="09:00",
            end_time="17:00"
        ),
        Availability(
            vendor_id="test_vendor_id",
            vertical_id="test_vertical_id",
            location_id="test_location_id",
            day_of_week=4,  # Friday
            start_time="09:00",
            end_time="17:00"
        ),
        Availability(
            vendor_id="test_vendor_id",
            vertical_id="test_vertical_id",
            location_id="test_location_id",
            day_of_week=5,  # Saturday
            start_time="09:00",
            end_time="17:00"
        ),
        Availability(
            vendor_id="test_vendor_id",
            vertical_id="test_vertical_id",
            location_id="test_location_id",
            day_of_week=6,  # Sunday
            start_time="09:00",
            end_time="17:00"
        )
    ]
    
    # Save to database
    for availability in test_availabilities:
        await engine.save(availability)
        print(f"Added availability for {availability.day_of_week}: {availability.start_time} - {availability.end_time}")
    
    print("Test availability data added successfully!")

if __name__ == "__main__":
    asyncio.run(add_test_availability())
