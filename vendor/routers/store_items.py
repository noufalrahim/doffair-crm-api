from fastapi import APIRouter, Depends, Query, File, UploadFile
from fastapi.responses import StreamingResponse
import pandas as pd
import io
from odmantic import AIOEngine
from typing import Optional, List

from core.database import get_engine
from core.security import get_current_vendor
from utils.response import success_response, error_response
from vendor.services.store_item_service import (
    create_store_item,
    get_store_item_by_id,
    list_store_items,
    update_store_item,
    delete_store_item,
    bulk_delete_store_items,
    bulk_create_store_items,
    count_store_items
)
from schemas.common import APIResponse
from vendor.schemas.store_item import (
    StoreItemCreate,
    StoreItemUpdate,
    StoreItemResponse,
    StoreItemListResponse
)

router = APIRouter(
    prefix="/vendor/store-items",
    tags=["Vendor - Store Items"]
)

@router.get("/public-template")
async def get_store_item_import_template():
    """
    Download a sample XLSX template for store item bulk import.
    """
    columns = [
        "sku", "name", "description", "category", 
        "stock_quantity", "unit", "base_price", 
        "manufacturer", "mfd_date", "expiry_date", 
        "is_active", "tags"
    ]
    
    # Create an empty DataFrame
    df = pd.DataFrame(columns=columns)
    
    # Add sample row
    sample_row = {
        "sku": "SKU-001",
        "name": "Organic Dog Food - 10kg",
        "description": "Premium organic dog food for adult dogs",
        "category": "Food",
        "stock_quantity": 50,
        "unit": "BAG",
        "base_price": 1200.00,
        "manufacturer": "HealthyPets Co",
        "mfd_date": "2026-01-01",
        "expiry_date": "2027-01-01",
        "is_active": True,
        "tags": "dog,food,organic"
    }
    df = pd.concat([df, pd.DataFrame([sample_row])], ignore_index=True)
    
    # Write to BytesIO
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Store Items')
    output.seek(0)
    
    headers = {
        'Content-Disposition': 'attachment; filename="store_item_import_template.xlsx"'
    }
    
    return StreamingResponse(
        output, 
        headers=headers, 
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@router.post("", response_model=APIResponse)
async def create_store_item_endpoint(
    data: StoreItemCreate,
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Create a new store item.
    """
    vendor_id = current_vendor["vendor_id"]
    store_item = await create_store_item(engine, vendor_id, data)
    
    response_data = StoreItemResponse(
        id=str(store_item.id),
        vendor_id=store_item.vendor_id,
        vertical_id=store_item.vertical_id,
        name=store_item.name,
        description=store_item.description,
        category=store_item.category,
        stock_quantity=store_item.stock_quantity,
        unit=store_item.unit,
        base_price=store_item.base_price,
        sku=store_item.sku,
        manufacturer=store_item.manufacturer,
        images=store_item.images,
        mfd_date=store_item.mfd_date,
        expiry_date=store_item.expiry_date,
        tags=store_item.tags,
        is_active=store_item.is_active,
        created_at=store_item.created_at,
        updated_at=store_item.updated_at
    )
    
    return success_response(
        message="Store item created successfully",
        data=response_data.model_dump()
    ).model_dump()

@router.get("", response_model=APIResponse)
async def list_store_items_endpoint(
    vertical_id: Optional[str] = Query(None, description="Filter by vertical ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search by name"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: Optional[int] = Query(None, ge=1, description="Number of items per page"),
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    List all store items for the vendor.
    """
    vendor_id = current_vendor["vendor_id"]
    
    # Calculate skip for pagination
    skip = (page - 1) * limit if limit else 0
    
    store_items = await list_store_items(engine, vendor_id, vertical_id, is_active, search, category, skip, limit)
    total_count = await count_store_items(engine, vendor_id, vertical_id, is_active, search, category)
    
    item_responses = [
        StoreItemResponse(
            id=str(i.id),
            vendor_id=i.vendor_id,
            vertical_id=i.vertical_id,
            name=i.name,
            description=i.description,
            category=i.category,
            stock_quantity=i.stock_quantity,
            unit=i.unit,
            base_price=i.base_price,
            sku=i.sku,
            manufacturer=i.manufacturer,
            images=i.images,
            mfd_date=i.mfd_date,
            expiry_date=i.expiry_date,
            tags=i.tags,
            is_active=i.is_active,
            created_at=i.created_at,
            updated_at=i.updated_at
        ).model_dump()
        for i in store_items
    ]
    
    response_data = StoreItemListResponse(
        total=total_count,
        items=item_responses
    )
    
    return success_response(
        message="Store items retrieved successfully",
        data=response_data.model_dump()
    ).model_dump()

@router.get("/{item_id}", response_model=APIResponse)
async def get_store_item_endpoint(
    item_id: str,
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Get detailed information about a specific store item.
    """
    vendor_id = current_vendor["vendor_id"]
    store_item = await get_store_item_by_id(engine, vendor_id, item_id)
    
    response_data = StoreItemResponse(
        id=str(store_item.id),
        vendor_id=store_item.vendor_id,
        vertical_id=store_item.vertical_id,
        name=store_item.name,
        description=store_item.description,
        category=store_item.category,
        stock_quantity=store_item.stock_quantity,
        unit=store_item.unit,
        base_price=store_item.base_price,
        sku=store_item.sku,
        manufacturer=store_item.manufacturer,
        images=store_item.images,
        mfd_date=store_item.mfd_date,
        expiry_date=store_item.expiry_date,
        tags=store_item.tags,
        is_active=store_item.is_active,
        created_at=store_item.created_at,
        updated_at=store_item.updated_at
    )
    
    return success_response(
        message="Store item retrieved successfully",
        data=response_data.model_dump()
    ).model_dump()

@router.patch("/{item_id}", response_model=APIResponse)
async def update_store_item_endpoint(
    item_id: str,
    data: StoreItemUpdate,
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Update an existing store item.
    """
    vendor_id = current_vendor["vendor_id"]
    store_item = await update_store_item(engine, vendor_id, item_id, data)
    
    response_data = StoreItemResponse(
        id=str(store_item.id),
        vendor_id=store_item.vendor_id,
        vertical_id=store_item.vertical_id,
        name=store_item.name,
        description=store_item.description,
        category=store_item.category,
        stock_quantity=store_item.stock_quantity,
        unit=store_item.unit,
        base_price=store_item.base_price,
        sku=store_item.sku,
        manufacturer=store_item.manufacturer,
        images=store_item.images,
        mfd_date=store_item.mfd_date,
        expiry_date=store_item.expiry_date,
        tags=store_item.tags,
        is_active=store_item.is_active,
        created_at=store_item.created_at,
        updated_at=store_item.updated_at
    )
    
    return success_response(
        message="Store item updated successfully",
        data=response_data.model_dump()
    ).model_dump()

@router.delete("/bulk", response_model=APIResponse)
async def bulk_delete_store_items_endpoint(
    item_ids: List[str] = Query(..., description="List of item IDs to delete"),
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Delete multiple store items at once.
    """
    vendor_id = current_vendor["vendor_id"]
    deleted_count = await bulk_delete_store_items(engine, vendor_id, item_ids)
    
    return success_response(
        message=f"Successfully deleted {deleted_count} items",
        data={"deleted_count": deleted_count}
    ).model_dump()

@router.delete("/{item_id}", response_model=APIResponse)
async def delete_store_item_endpoint(
    item_id: str,
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Delete a store item.
    """
    vendor_id = current_vendor["vendor_id"]
    await delete_store_item(engine, vendor_id, item_id)
    
    return success_response(
        message="Store item deleted successfully",
        data={"item_id": item_id, "deleted": True}
    ).model_dump()



@router.post("/bulk-import", response_model=APIResponse)
async def bulk_import_store_items_endpoint(
    file: UploadFile = File(...),
    vertical_id: str = Query(...),
    current_vendor: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine)
):
    """
    Bulk import store items from CSV or XLSX file.
    """
    vendor_id = current_vendor["vendor_id"]
    
    contents = await file.read()
    if file.filename.endswith('.csv'):
        df = pd.read_csv(io.BytesIO(contents))
    elif file.filename.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(io.BytesIO(contents))
    else:
        return error_response(message="Unsupported file format. Please upload CSV or XLSX.")
    
    # Replace NaN with None
    df = df.where(pd.notnull(df), None)
    
    items_data = df.to_dict(orient='records')
    
    for item in items_data:
        item['vertical_id'] = vertical_id
        
    try:
        items = await bulk_create_store_items(engine, vendor_id, items_data)
        
        return success_response(
            message=f"Successfully processed import. {len(items)} store items imported.",
            data={"imported_count": len(items), "received_count": len(items_data)}
        ).model_dump()
    except Exception as e:
        print(f"ERROR: Bulk import failed: {e}")
        return error_response(message=f"Bulk import failed: {str(e)}")
