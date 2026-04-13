from fastapi import APIRouter, Depends, HTTPException, Body
from odmantic import AIOEngine, ObjectId
from typing import List, Optional
from datetime import datetime

from core.database import get_engine
from core.security import require_user
from user.models.cart import Cart, CartItem
from user.models.coupon import Coupon
from vendor.models.store_item import StoreItem
from user.schemas.cart import (
    CartResponse, 
    CartItemAdd, 
    CartItemResponse,
    ApplyCouponRequest,
    CartDeleteResponse
)
from schemas.common import APIResponse
from utils.response import success_response

router = APIRouter(
    prefix="/user/cart",
    tags=["User - Cart"]
)

async def get_or_create_cart(user_id: str, engine: AIOEngine) -> Cart:
    cart = await engine.find_one(Cart, Cart.user_id == user_id)
    if not cart:
        cart = Cart(user_id=user_id)
        await engine.save(cart)
    return cart

@router.get("", response_model=APIResponse)
async def get_cart(
    token: dict = Depends(require_user),
    engine: AIOEngine = Depends(get_engine)
):
    user_id = token["sub"]
    cart = await get_or_create_cart(user_id, engine)
    
    item_responses = []
    total_price = 0.0
    
    for item in cart.items:
        subtotal = item.price * item.quantity
        total_price += subtotal
        item_responses.append(CartItemResponse(
            product_id=item.product_id,
            vendor_id=item.vendor_id,
            name=item.name,
            price=item.price,
            quantity=item.quantity,
            image=item.image,
            subtotal=subtotal
        ))
        
    discount_amount = 0.0
    if cart.coupon_code:
        coupon = await engine.find_one(Coupon, Coupon.code == cart.coupon_code, Coupon.is_active == True)
        if coupon:
            if total_price >= coupon.min_order_value:
                if coupon.discount_type == "percentage":
                    discount_amount = (total_price * coupon.discount_value) / 100
                else:
                    discount_amount = coupon.discount_value
                
                if coupon.max_discount_amount:
                    discount_amount = min(discount_amount, coupon.max_discount_amount)
            else:
                # Coupon not valid anymore due to total price
                cart.coupon_code = None
                await engine.save(cart)
                discount_amount = 0.0
        else:
            cart.coupon_code = None
            await engine.save(cart)
            discount_amount = 0.0
            
    grand_total = max(0, total_price - discount_amount)
    
    data = {
        "items": item_responses,
        "coupon_code": cart.coupon_code,
        "total_items": sum(i.quantity for i in cart.items),
        "total_price": total_price,
        "discount_amount": discount_amount,
        "grand_total": grand_total
    }
    
    return success_response(data=data)

@router.post("/items", response_model=APIResponse)
async def add_to_cart(
    data: CartItemAdd,
    token: dict = Depends(require_user),
    engine: AIOEngine = Depends(get_engine)
):
    user_id = token["sub"]
    cart = await get_or_create_cart(user_id, engine)
    
    try:
        obj_id = ObjectId(data.product_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product ID")
        
    product = await engine.find_one(StoreItem, StoreItem.id == obj_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    # Check if item already in cart
    existing_item = next((i for i in cart.items if i.product_id == data.product_id), None)
    if existing_item:
        existing_item.quantity += data.quantity
    else:
        cart.items.append(CartItem(
            product_id=str(product.id),
            vendor_id=product.vendor_id,
            quantity=data.quantity,
            name=product.name,
            price=product.base_price,
            image=product.images[0] if product.images else None
        ))
        
    cart.updated_at = datetime.utcnow()
    await engine.save(cart)
    
    return await get_cart(token, engine)

@router.delete("/items/{product_id}", response_model=APIResponse)
async def remove_from_cart(
    product_id: str,
    token: dict = Depends(require_user),
    engine: AIOEngine = Depends(get_engine)
):
    user_id = token["sub"]
    cart = await get_or_create_cart(user_id, engine)
    
    cart.items = [i for i in cart.items if i.product_id != product_id]
    cart.updated_at = datetime.utcnow()
    await engine.save(cart)
    
    return await get_cart(token, engine)

@router.delete("", response_model=CartDeleteResponse)
async def delete_cart(
    token: dict = Depends(require_user),
    engine: AIOEngine = Depends(get_engine)
):
    user_id = token["sub"]
    cart = await engine.find_one(Cart, Cart.user_id == user_id)
    if cart:
        await engine.delete(cart)
        
    return success_response(message="Cart deleted successfully")

@router.post("/apply-coupon", response_model=APIResponse)
async def apply_coupon(
    data: ApplyCouponRequest,
    token: dict = Depends(require_user),
    engine: AIOEngine = Depends(get_engine)
):
    user_id = token["sub"]
    cart = await get_or_create_cart(user_id, engine)
    
    coupon = await engine.find_one(Coupon, Coupon.code == data.code, Coupon.is_active == True)
    if not coupon:
        raise HTTPException(status_code=400, detail="Invalid coupon code")
        
    # Check if coupon expired
    if coupon.end_date < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Coupon expired")
        
    # Check min order value
    total_price = sum(item.price * item.quantity for item in cart.items)
    if total_price < coupon.min_order_value:
        raise HTTPException(status_code=400, detail=f"Minimum order value for this coupon is {coupon.min_order_value}")
        
    cart.coupon_code = coupon.code
    cart.updated_at = datetime.utcnow()
    await engine.save(cart)
    
    return await get_cart(token, engine)
