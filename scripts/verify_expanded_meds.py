import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

async def verify():
    load_dotenv()
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME")
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    col = db['medications']

    print("Verifying medications with expanded fields...")
    
    # Check one sample
    doc = await col.find_one({"vendor_id": "69947d80f7f198a8f13efebf", "name": "Amoxyclav 625"})
    if doc:
        print(f"Sample Product Found: {doc.get('name')}")
        print(f" - Medicine ID: {doc.get('medicine_id')}")
        print(f" - Status: {doc.get('status')}")
        print(f" - Image URL: {doc.get('image_url')}")
        print(f" - Is Expired: {doc.get('is_expired')}")
        print(f" - Generic Composition: {doc.get('generic_composition')}")
        print(f" - Dosage Form: {doc.get('dosage_form')}")
        print(f" - Species: {doc.get('species')}")
        print(f" - Is Prescription Required: {doc.get('is_prescription_required')}")
        print(f" - Batch ID: {doc.get('batch_id')}")
        print(f" - Barcode: {doc.get('barcode')}")
    else:
        print("Sample not found!")

    vendors = ["69947d80f7f198a8f13efebf", "69905d49c857901ed124f37b"]
    for vid in vendors:
        vcount = await col.count_documents({"vendor_id": vid})
        print(f"Vendor {vid}: {vcount} medicines")

if __name__ == "__main__":
    asyncio.run(verify())
