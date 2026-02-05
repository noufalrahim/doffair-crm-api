"""
Utility Script: Create Completed Booking for Invoice Testing
============================================================

This script automates the process of creating a completed booking
so you can quickly test the invoice generation feature.

Usage:
    python scripts/create_completed_booking.py

What it does:
1. Creates a user account (if needed)
2. Creates a vendor account (if needed)
3. Creates a service
4. Creates a booking
5. Marks booking as COMPLETED
6. Returns booking_id for invoice testing
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
from bson import ObjectId

from user.models.user import User
from user.models.booking import Booking
from vendor.models.vendor import Vendor
from vendor.models.vendor_location import VendorLocation
from vendor.models.vendor_service import VendorService
from vendor.models.service_pricing import ServicePricing
from admin.models.service_type import ServiceType
from core.enums import (
    BookingStatus,
    VendorStatus,
    ServiceDeliveryMode,
    DiscountType
)
from core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_completed_booking_for_testing(vendor_id: Optional[str] = None):
    """
    Create a completed booking with all required data
    
    Args:
        vendor_id: Optional specific vendor ID to use. If None, finds or creates test vendor.
    """
    # Connect to database
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    engine = AIOEngine(client=client, database=settings.MONGODB_DB_NAME)
    
    logger.info("🚀 Starting completed booking creation...")
    
    try:
        # ============================================
        # 1. Find or Create Service Type
        # ============================================
        service_type = await engine.find_one(ServiceType, ServiceType.is_active == True)
        if not service_type:
            service_type = ServiceType(
                code="pet_grooming",
                display_name="Pet Grooming",
                description="Professional pet grooming services",
                mode=ServiceMode.BOOKING,
                is_active=True
            )
            await engine.save(service_type)
            logger.info(f"✅ Created service type: {service_type.display_name}")
        else:
            logger.info(f"✅ Using existing service type: {service_type.display_name}")
        
        # ============================================
        # 2. Find or Create Vendor
        # ============================================
        if vendor_id:
            # Use specified vendor ID
            vendor = await engine.find_one(Vendor, Vendor.id == ObjectId(vendor_id))
            if not vendor:
                raise Exception(f"Vendor {vendor_id} not found")
            logger.info(f"✅ Using specified vendor: {vendor.legal_name} ({vendor_id})")
        else:
            # Find or create test vendor
            vendor = await engine.find_one(
                Vendor,
                (Vendor.status == VendorStatus.APPROVED) | (Vendor.status == VendorStatus.PRICING_CONFIGURED)
            )
            
            if not vendor:
                import random
                random_suffix = random.randint(1000, 9999)
                vendor = Vendor(
                    primary_contact_phone=f"+9198765{random_suffix}",
                    primary_contact_email=f"test.vendor.{random_suffix}@example.com",
                    password_hash="dummy_hash_for_testing",
                    legal_name="Test Pet Salon Pvt Ltd",
                    status=VendorStatus.APPROVED
                )
                await engine.save(vendor)
                logger.info(f"✅ Created vendor: {vendor.legal_name}")
            else:
                logger.info(f"✅ Using existing vendor: {vendor.legal_name}")
            
            vendor_id = str(vendor.id)
        
        # ============================================
        # 3. Create Vendor Location
        # ============================================
        location = await engine.find_one(
            VendorLocation,
            VendorLocation.vendor_id == vendor_id
        )
        
        if not location:
            location = VendorLocation(
                vendor_id=vendor_id,
                name="Main Branch",
                address_line_1="123 Test Street",
                city="Hyderabad",
                state="Telangana",
                pincode="500084",
                country="India",
                latitude=17.385044,
                longitude=78.486671,
                is_primary=True
            )
            await engine.save(location)
            logger.info(f"✅ Created location: {location.name}")
        else:
            logger.info(f"✅ Using existing location: {location.name}")
        
        location_id = str(location.id)
        
        # ============================================
        # 4. Create Vendor Service
        # ============================================
        service = await engine.find_one(
            VendorService,
            (VendorService.vendor_id == vendor_id) &
            (VendorService.location_id == location_id) &
            (VendorService.service_type_id == str(service_type.id))
        )
        
        if not service:
            service = VendorService(
                vendor_id=vendor_id,
                location_id=location_id,
                service_type_id=str(service_type.id),
                name="Basic Grooming Package",
                service_kind="BASE",
                delivery_mode=ServiceDeliveryMode.CENTER,
                is_active=True
            )
            await engine.save(service)
            logger.info(f"✅ Created service: {service.name}")
        else:
            logger.info(f"✅ Using existing service: {service.name}")
        
        service_id = str(service.id)
        
        # ============================================
        # 5. Create Service Pricing
        # ============================================
        pricing = await engine.find_one(
            ServicePricing,
            (ServicePricing.service_id == service_id) &
            (ServicePricing.vendor_id == vendor_id)
        )
        
        if not pricing:
            pricing = ServicePricing(
                vendor_id=vendor_id,
                service_id=service_id,
                location_id=location_id,
                base_price=500.0,
                discount_type=DiscountType.FLAT,
                discount_value=50.0,
                is_active=True
            )
            await engine.save(pricing)
            logger.info(f"✅ Created pricing: Base ₹{pricing.base_price}, Discount ₹{pricing.discount_value}")
        else:
            logger.info(f"✅ Using existing pricing: Base ₹{pricing.base_price}")
        
        # ============================================
        # 6. Create User for testing
        # ============================================
        # Always create fresh user for testing to avoid schema conflicts
        import random
        random_suffix = random.randint(1000, 9999)
        
        user = User(
            phone=f"+9191234{random_suffix}",
            email=f"test.user.{random_suffix}@example.com",
            name="Test User",
            password_hash="dummy_hash_for_testing",
            is_verified=True
        )
        await engine.save(user)
        logger.info(f"✅ Created user: {user.name}")
        
        user_id = str(user.id)
        
        # ============================================
        # 7. Create Booking
        # ============================================
        booking_date = datetime.utcnow() + timedelta(days=1)
        
        booking = Booking(
            user_id=user_id,
            vendor_id=vendor_id,
            service_id=service_id,
            service_type_id=str(service_type.id),
            location_id=location_id,
            
            # Cached info
            user_name=user.name,
            user_phone=user.phone,
            user_email=user.email,
            vendor_name=vendor.legal_name or f"Vendor {vendor_id[:8]}",
            vendor_phone=vendor.primary_contact_phone,
            vendor_email=vendor.primary_contact_email,
            service_name=service.name,
            service_type_name=service_type.display_name,
            
            # Booking details
            booking_date=booking_date,
            delivery_mode="CENTER",
            
            # Pricing
            base_amount=pricing.base_price,
            discount_amount=pricing.discount_value,
            final_amount=pricing.base_price - pricing.discount_value,
            
            # Status - Create directly as COMPLETED for invoice testing
            status=BookingStatus.COMPLETED,
            vendor_notes="Test booking for invoice generation"
        )
        
        await engine.save(booking)
        logger.info(f"✅ Created booking: {str(booking.id)}")
        logger.info(f"✅ Booking status: COMPLETED")
        
        # ============================================
        # DONE - Return Details
        # ============================================
        logger.info("\n" + "="*60)
        logger.info("🎉 COMPLETED BOOKING CREATED SUCCESSFULLY!")
        logger.info("="*60)
        logger.info(f"\n📋 BOOKING DETAILS:")
        logger.info(f"   Booking ID: {str(booking.id)}")
        logger.info(f"   Customer: {booking.user_name}")
        logger.info(f"   Vendor: {booking.vendor_name}")
        logger.info(f"   Service: {booking.service_name}")
        logger.info(f"   Amount: ₹{booking.final_amount}")
        logger.info(f"   Status: {booking.status}")
        logger.info(f"\n🧾 NOW YOU CAN TEST INVOICE GENERATION:")
        logger.info(f"   POST /vendor/invoices/generate")
        logger.info(f"   {{")
        logger.info(f'     "booking_id": "{str(booking.id)}",')
        logger.info(f'     "due_days": 30,')
        logger.info(f'     "auto_send": true')
        logger.info(f"   }}")
        logger.info(f"\n✅ Use this booking_id: {str(booking.id)}")
        logger.info("="*60 + "\n")
        
        return {
            "booking_id": str(booking.id),
            "vendor_id": vendor_id,
            "user_id": user_id,
            "service_id": service_id,
            "amount": booking.final_amount,
            "status": booking.status
        }
        
    except Exception as e:
        logger.error(f"❌ Error creating completed booking: {str(e)}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    import sys
    
    logger.info("="*60)
    logger.info("COMPLETED BOOKING CREATION SCRIPT")
    logger.info("="*60)
    
    # Check for vendor_id argument
    vendor_id = None
    if len(sys.argv) > 1:
        vendor_id = sys.argv[1]
        logger.info(f"Using vendor_id from argument: {vendor_id}")
    
    result = asyncio.run(create_completed_booking_for_testing(vendor_id))
    
    logger.info("\n✅ Script execution completed successfully!")
    logger.info(f"📋 Booking ID: {result['booking_id']}")
