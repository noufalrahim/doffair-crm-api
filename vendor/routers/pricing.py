from fastapi import APIRouter, Depends, HTTPException
from odmantic import AIOEngine

from core.database import get_engine
from core.security import require_vendor
from utils.response import success_response

from vendor.schemas.pricing import PricingCreateRequest
from vendor.services.pricing_service import upsert_pricing
from vendor.utils.pricing import calculate_final_price


router = APIRouter(
    prefix="/vendor/onboarding",
    tags=["Vendor Onboarding - Pricing"],
)


@router.post("/pricing")
async def configure_pricing(
    payload: PricingCreateRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    vendor_id = token["vendor_id"]

    print("O my god")
    service = await upsert_pricing(engine, vendor_id, payload)

    return success_response(
        message="Pricing configured successfully",
        data={
            "service_id": str(service.id),
            "location_id": service.location_id,
            "base_price": service.base_price,
            "discount_type": service.discount_type,
            "discount_value": service.discount_value,
            "final_price": calculate_final_price(
                service.base_price,
                service.discount_type,
                service.discount_value,
            ),
        },
    )
