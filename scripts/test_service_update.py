"""
Test Service Update Endpoint
Diagnostic script to identify the 500 error
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
from vendor.models.vendor_service import VendorService
from vendor.schemas.service import VendorServiceUpdateRequest
from vendor.services.service_service import update_service
import logging
from bson import ObjectId

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_service_update():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    engine = AIOEngine(client=client, database=settings.MONGODB_DB_NAME)
    
    try:
        logger.info("🔍 Finding a service to test update...")
        
        # Find any service
        service = await engine.find_one(VendorService)
        if not service:
            logger.error("❌ No services found in database")
            return
        
        vendor_id = service.vendor_id
        service_id = str(service.id)
        
        logger.info(f"✅ Found service: {service.name}")
        logger.info(f"   Vendor ID: {vendor_id}")
        logger.info(f"   Service ID: {service_id}")
        
        # Test 1: Update with name only
        logger.info("\n📝 Test 1: Update service name...")
        try:
            payload = VendorServiceUpdateRequest(
                name="Updated Service Name Test"
            )
            logger.info(f"   Payload created: {payload}")
            logger.info(f"   Payload dict: {payload.model_dump(exclude_unset=True)}")
            
            updated = await update_service(engine, vendor_id, service_id, payload)
            logger.info(f"✅ Test 1 PASSED: Name updated to '{updated.name}'")
        except Exception as e:
            logger.error(f"❌ Test 1 FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Test 2: Update with pricing fields
        logger.info("\n📝 Test 2: Update pricing fields...")
        try:
            payload = VendorServiceUpdateRequest(
                base_price=600.0,
                discount_value=100.0
            )
            logger.info(f"   Payload created: {payload}")
            logger.info(f"   Payload dict: {payload.model_dump(exclude_unset=True)}")
            
            updated = await update_service(engine, vendor_id, service_id, payload)
            logger.info(f"✅ Test 2 PASSED: Service updated")
            
            # Check pricing
            pricing = await engine.find_one(
                VendorService,
                (VendorService.id == ObjectId(service_id)) & (VendorService.vendor_id == vendor_id)
            )
            if pricing:
                logger.info(f"   Pricing: ₹{pricing.base_price}, Discount: ₹{pricing.discount_value}")
            
        except Exception as e:
            logger.error(f"❌ Test 2 FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Test 3: Update with is_active
        logger.info("\n📝 Test 3: Update is_active field...")
        try:
            payload = VendorServiceUpdateRequest(
                is_active=False
            )
            logger.info(f"   Payload created: {payload}")
            logger.info(f"   Payload dict: {payload.model_dump(exclude_unset=True)}")
            
            updated = await update_service(engine, vendor_id, service_id, payload)
            logger.info(f"✅ Test 3 PASSED: is_active = {updated.is_active}")
        except Exception as e:
            logger.error(f"❌ Test 3 FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Test 4: Mixed update
        logger.info("\n📝 Test 4: Mixed update (name + pricing)...")
        try:
            payload = VendorServiceUpdateRequest(
                name="Final Test Service",
                base_price=500.0,
                discount_type="FLAT",
                discount_value=50.0,
                is_active=True
            )
            logger.info(f"   Payload created: {payload}")
            logger.info(f"   Payload dict: {payload.model_dump(exclude_unset=True)}")
            
            updated = await update_service(engine, vendor_id, service_id, payload)
            logger.info(f"✅ Test 4 PASSED: Service fully updated")
            logger.info(f"   Name: {updated.name}")
            logger.info(f"   Active: {updated.is_active}")
            
        except Exception as e:
            logger.error(f"❌ Test 4 FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
        
        logger.info("\n" + "="*60)
        logger.info("✅ DIAGNOSTIC COMPLETE")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ Diagnostic script error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(test_service_update())
