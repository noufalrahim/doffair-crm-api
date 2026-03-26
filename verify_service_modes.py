import asyncio
# import httpx
from odmantic import ObjectId

async def verify_service_modes():
    base_url = "http://localhost:8000"
    
    # We need a valid vendor token. For testing, we might need to mock or 
    # use an existing one if available. But since this is a local dev env,
    # we can try to find a vendor_id and use a mock token if the security allows it,
    # or just test the model/logic directly if we want to be safe.
    
    # Better approach: Create a script that uses the engine directly like debug_db.py
    # to verify the model and service functions work as expected.
    
    from motor.motor_asyncio import AsyncIOMotorClient
    from odmantic import AIOEngine
    from vendor.models.vendor_service import VendorService
    from core.enums import ServiceDeliveryMode
    from vendor.schemas.service import BaseServiceCreateRequest, ComboServiceCreateRequest, VendorServiceUpdateRequest
    from vendor.services.service_service import create_base_service, create_combo_service, update_service
    
    uri = "mongodb+srv://doffair_dev:yTwgZQf2t3XiSXos@development-cluster.9w53x.mongodb.net/?retryWrites=true&w=majority&appName=development-cluster"
    client = AsyncIOMotorClient(uri)
    engine = AIOEngine(client=client, database="doffair_vendors_new")
    
    test_vendor_id = "679883500d0fc8787834511d" # Example vendor ID
    test_location_id = "679c855a794772b1d30fb4df"
    test_vertical_id = "6799fc990b795697621c469b"
    
    print("Testing Base Service Creation with BOTH...")
    base_payload = BaseServiceCreateRequest(
        location_id=test_location_id,
        vertical_id=test_vertical_id,
        name="Test Multi-Mode Service",
        delivery_mode=ServiceDeliveryMode.BOTH,
        base_price=100.0,
        images=[]
    )
    
    service = await create_base_service(engine, test_vendor_id, base_payload)
    print(f"Created Base Service: {service.id}, Mode: {service.delivery_mode}")
    assert service.delivery_mode == ServiceDeliveryMode.BOTH
    
    print("\nTesting Combo Service Creation with BOTH...")
    combo_payload = ComboServiceCreateRequest(
        location_id=test_location_id,
        vertical_id=test_vertical_id,
        name="Test Multi-Mode Combo",
        delivery_mode=ServiceDeliveryMode.BOTH,
        included_service_ids=[str(service.id)],
        base_price=150.0,
        images=[]
    )
    
    combo = await create_combo_service(engine, test_vendor_id, combo_payload)
    print(f"Created Combo Service: {combo.id}, Mode: {combo.delivery_mode}")
    assert combo.delivery_mode == ServiceDeliveryMode.BOTH
    
    print("\nTesting Service Update to CENTER...")
    update_payload = VendorServiceUpdateRequest(
        delivery_mode=ServiceDeliveryMode.CENTER
    )
    
    updated_service = await update_service(engine, test_vendor_id, str(service.id), update_payload)
    print(f"Updated Service: {updated_service.id}, Mode: {updated_service.delivery_mode}")
    assert updated_service.delivery_mode == ServiceDeliveryMode.CENTER
    
    print("\nCleanup...")
    await engine.delete(service)
    await engine.delete(combo)
    print("Verification Successful!")

if __name__ == "__main__":
    asyncio.run(verify_service_modes())
