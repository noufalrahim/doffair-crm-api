from fastapi import APIRouter, Depends, Query, HTTPException
from odmantic import AIOEngine, ObjectId
from typing import Optional, List
import re

from core.database import get_engine
from vendor.models.store_item import StoreItem
from vendor.models.vendor import Vendor
from user.models.coupon import Coupon
from schemas.common import APIResponse
from user.schemas.marketplace import (
    MarketplaceSearchResponse, 
    ProductResponse, 
    StoreResponse,
    FilterResponse,
    CouponResponse,
    StoreDetailsResponse,
    StoreProductsResponse,
    ProductDetailsResponse,
    CouponListResponse
)
from utils.response import success_response

router = APIRouter(
    prefix="/user/marketplace",
    tags=["User - Marketplace"]
)

@router.get("/search", response_model=MarketplaceSearchResponse)
async def search_marketplace(
    query: str = Query(..., description="Search query for products or stores"),
    engine: AIOEngine = Depends(get_engine)
):
    # Regex for case-insensitive search
    search_pattern = f"(?i).*{query}.*"
    
    # Search products
    products_db = await engine.find(
        StoreItem, 
        (StoreItem.name.match(search_pattern)) | 
        (StoreItem.tags.match(search_pattern)),
        StoreItem.is_active == True
    )
    
    # Search stores (vendors)
    stores_db = await engine.find(
        Vendor,
        (Vendor.legal_name.match(search_pattern)) |
        (Vendor.about.match(search_pattern)),
        Vendor.is_active == True
    )
    
    products = [
        ProductResponse(
            id=str(p.id),
            vendor_id=p.vendor_id,
            name=p.name,
            description=p.description,
            category=p.category,
            base_price=p.base_price,
            images=p.images,
            stock_quantity=p.stock_quantity,
            is_active=p.is_active
        ) for p in products_db
    ]
    
    stores = [
        StoreResponse(
            id=str(s.id),
            legal_name=s.legal_name,
            about=s.about,
            logo=s.logo_blob_path,
            rating=s.overall_rating,
            is_verified=s.is_verified
        ) for s in stores_db
    ]
    
    return success_response(data={"products": products, "stores": stores})

@router.get("/stores/{vendor_id}", response_model=StoreDetailsResponse)
async def get_store_details(
    vendor_id: str,
    engine: AIOEngine = Depends(get_engine)
):
    try:
        obj_id = ObjectId(vendor_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid vendor ID")
        
    vendor = await engine.find_one(Vendor, Vendor.id == obj_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Store not found")
        
    return success_response(data=StoreResponse(
        id=str(vendor.id),
        legal_name=vendor.legal_name,
        about=vendor.about,
        logo=vendor.logo_blob_path,
        rating=vendor.overall_rating,
        is_verified=vendor.is_verified
    ))

@router.get("/stores/{vendor_id}/products", response_model=StoreProductsResponse)
async def get_store_products(
    vendor_id: str,
    category: Optional[str] = None,
    engine: AIOEngine = Depends(get_engine)
):
    query = [StoreItem.vendor_id == vendor_id, StoreItem.is_active == True]
    if category:
        query.append(StoreItem.category == category)
        
    products_db = await engine.find(StoreItem, *query)
    
    products = [
        ProductResponse(
            id=str(p.id),
            vendor_id=p.vendor_id,
            name=p.name,
            description=p.description,
            category=p.category,
            base_price=p.base_price,
            images=p.images,
            stock_quantity=p.stock_quantity,
            is_active=p.is_active
        ) for p in products_db
    ]
    
    return success_response(data=products)

@router.get("/products/{product_id}", response_model=ProductDetailsResponse)
async def get_product_details(
    product_id: str,
    engine: AIOEngine = Depends(get_engine)
):
    try:
        obj_id = ObjectId(product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product ID")
        
    product = await engine.find_one(StoreItem, StoreItem.id == obj_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    return success_response(data=ProductResponse(
        id=str(product.id),
        vendor_id=product.vendor_id,
        name=product.name,
        description=product.description,
        category=product.category,
        base_price=product.base_price,
        images=product.images,
        stock_quantity=product.stock_quantity,
        is_active=product.is_active
    ))

@router.get("/filters", response_model=FilterResponse)
async def get_marketplace_filters(
    engine: AIOEngine = Depends(get_engine)
):
    all_products = await engine.find(StoreItem, StoreItem.is_active == True)
    categories = list(set([p.category for p in all_products]))
    
    prices = [p.base_price for p in all_products]
    price_min = min(prices) if prices else 0
    price_max = max(prices) if prices else 0
    
    vendors_db = await engine.find(Vendor, Vendor.is_active == True, limit=10)
    vendors = [
        StoreResponse(
            id=str(v.id),
            legal_name=v.legal_name,
            about=v.about,
            logo=v.logo_blob_path,
            rating=v.overall_rating,
            is_verified=v.is_verified
        ) for v in vendors_db
    ]
    
    return success_response(data={
        "categories": categories,
        "price_min": price_min,
        "price_max": price_max,
        "vendors": vendors
    })

@router.get("/coupons", response_model=CouponListResponse)
async def get_coupons(
    vendor_id: Optional[str] = None,
    engine: AIOEngine = Depends(get_engine)
):
    query = [Coupon.is_active == True]
    if vendor_id:
        query.append((Coupon.vendor_id == vendor_id) | (Coupon.vendor_id == None))
    else:
        query.append(Coupon.vendor_id == None)
        
    coupons_db = await engine.find(Coupon, *query)
    
    coupons = [
        CouponResponse(
            id=str(c.id),
            code=c.code,
            description=c.description,
            discount_type=c.discount_type,
            discount_value=c.discount_value,
            min_order_value=c.min_order_value,
            end_date=c.end_date
        ) for c in coupons_db
    ]
    
    return success_response(data=coupons)
