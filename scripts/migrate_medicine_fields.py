import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def migrate_medications():
    load_dotenv()
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    col = db['medications']

    print("Migrating existing medications to include new fields...")
    
    # Fields with default False
    await col.update_many(
        {"is_prescription_required": {"$exists": False}},
        {"$set": {"is_prescription_required": False}}
    )
    await col.update_many(
        {"near_expiry_flag": {"$exists": False}},
        {"$set": {"near_expiry_flag": False}}
    )
    await col.update_many(
        {"is_expired": {"$exists": False}},
        {"$set": {"is_expired": False}}
    )
    await col.update_many(
        {"status": {"$exists": False}},
        {"$set": {"status": "Active"}}
    )
    
    # Other important fields with default None/empty
    fields_to_init = {
        "medicine_id": None,
        "image_url": None,
        "brand_name": None,
        "generic_composition": None,
        "dosage_form": None,
        "strength": None,
        "species": None,
        "indications": None,
        "contraindications": None,
        "side_effects": None,
        "drug_interactions": None,
        "storage_instructions": None,
        "schedule_class": None,
        "barcode": None,
        "qr_code": None,
        "purchase_price": None,
        "selling_price": None,
        "supplier_name": None,
        "supplier_contact": None,
        "last_restocked_date": None,
        "pack_size": None,
        "units_per_pack": None,
        "reorder_level": None,
        "reorder_quantity": None,
        "location": None
    }
    
    for field, default in fields_to_init.items():
        await col.update_many(
            {field: {"$exists": False}},
            {"$set": {field: default}}
        )

    print("Migration finished!")

if __name__ == "__main__":
    asyncio.run(migrate_medications())
