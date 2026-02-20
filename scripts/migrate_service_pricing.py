import asyncio
import os
import sys
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_engine

async def migrate():
    engine = get_engine()
    db = engine.database

    print("Starting migration from service_pricing to vendor_services...")

    pricing_cursor = db.get_collection("service_pricing").find({})
    
    count = 0
    updated_count = 0
    error_count = 0
    
    async for pricing in pricing_cursor:
        count += 1
        service_id_str = pricing.get("service_id")
        if not service_id_str:
            print(f"Skipping pricing doc without service_id: {pricing['_id']}")
            error_count += 1
            continue
            
        try:
            service_id = ObjectId(service_id_str)
        except Exception:
            print(f"Invalid service_id format {service_id_str} in pricing doc {pricing['_id']}")
            error_count += 1
            continue

        base_price = pricing.get("base_price", 0.0)
        discount_type = pricing.get("discount_type", "NONE")
        discount_value = pricing.get("discount_value", None)
        is_active = pricing.get("is_active", True)
        
        if hasattr(discount_type, 'value'):
            discount_type = discount_type.value
        
        result = await db.get_collection("vendor_services").update_one(
            {"_id": service_id},
            {"$set": {
                "base_price": float(base_price),
                "discount_type": str(discount_type),
                "discount_value": float(discount_value) if discount_value is not None else None,
                "is_active": bool(is_active)
            }}
        )
        
        if result.modified_count > 0:
            updated_count += 1
        elif result.matched_count == 0:
            print(f"Warning: Service not found for pricing doc {pricing['_id']} with service_id {service_id}")
            error_count += 1

    print(f"Migration complete. Processed {count} docs. Updated {updated_count} services. Errors: {error_count}")
    print("Dropping service_pricing collection...")
    await db.drop_collection("service_pricing")
    print("Dropped service_pricing collection.")

if __name__ == "__main__":
    asyncio.run(migrate())
