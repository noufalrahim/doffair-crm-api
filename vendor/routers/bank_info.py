from fastapi import APIRouter, Depends, status
from odmantic import AIOEngine
from typing import Optional, Any

from core.database import get_engine
from core.security import get_current_vendor
from vendor.schemas.bank_info import (
    BankInfoCreateRequest, 
    BankInfoResponse, 
    BankInfoUpdateRequest,
    BankInfoAPIResponse
)
from vendor.services import bank_info_service
from utils.response import success_response
from schemas.common import APIResponse

# REMOVED PREFIX TO AVOID AMBIGUITY
router = APIRouter(tags=["Vendor - Bank Info"])

def _serialize(bank_info) -> dict:
    """Helper to serialize a BankInfo model to a dict for API response."""
    if not bank_info:
        return None
    return {
        "id": str(bank_info.id),
        "vendor_id": bank_info.vendor_id,
        "bank_name": bank_info.bank_name,
        "account_number": bank_info.account_number,
        "ifsc_code": bank_info.ifsc_code,
        "account_holder_name": bank_info.account_holder_name,
        "branch_name": bank_info.branch_name,
        "is_verified": bank_info.is_verified,
        "created_at": bank_info.created_at.isoformat(),
        "updated_at": bank_info.updated_at.isoformat(),
    }

# EXPLICIT PATH FOR SWAGGER VISIBILITY AND NO TRAILING SLASH
@router.post(
    "/vendor/bank-info", 
    status_code=status.HTTP_201_CREATED,
    summary="Create or Update Bank Information",
    description="Saves or updates the bank details for the authenticated vendor.",
    response_model=BankInfoAPIResponse,
)
async def create_or_update_bank_info(
    body: BankInfoCreateRequest,
    token: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine),
):
    """Create or update bank information for the authenticated vendor."""
    vendor_id = token.get("vendor_id")
    bank_info = await bank_info_service.create_or_update_bank_info(
        engine=engine,
        vendor_id=vendor_id,
        bank_name=body.bank_name,
        account_number=body.account_number,
        ifsc_code=body.ifsc_code,
        account_holder_name=body.account_holder_name,
        branch_name=body.branch_name,
    )
    return success_response(
        data=_serialize(bank_info),
        message="Bank information saved successfully"
    )

@router.patch(
    "/vendor/bank-info",
    summary="Partially Update Bank Information",
    description="Updates specific fields of the bank details for the authenticated vendor.",
    response_model=BankInfoAPIResponse,
)
async def update_bank_info(
    body: BankInfoUpdateRequest,
    token: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine),
):
    """Partially update bank information for the authenticated vendor."""
    vendor_id = token.get("vendor_id")
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        return success_response(message="No fields to update", success=True)
        
    try:
        bank_info = await bank_info_service.update_bank_info(
            engine=engine,
            vendor_id=vendor_id,
            update_data=update_data,
        )
        return success_response(
            data=_serialize(bank_info),
            message="Bank information updated successfully"
        )
    except Exception:
        return success_response(data=None, message="Bank information not found")

@router.patch(
    "/vendor/bank-info/{bank_info_id}",
    summary="Partially Update Bank Information by ID",
    description="Updates specific fields of a bank record identified by its ID for the authenticated vendor.",
    response_model=BankInfoAPIResponse,
)
async def update_bank_info_by_id(
    bank_info_id: str,
    body: BankInfoUpdateRequest,
    token: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine),
):
    """Partially update bank information by ID for the authenticated vendor."""
    vendor_id = token.get("vendor_id")
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        return success_response(message="No fields to update")

    try:
        bank_info = await bank_info_service.update_bank_info_by_id(
            engine=engine,
            bank_info_id=bank_info_id,
            vendor_id=vendor_id,
            update_data=update_data,
        )
        return success_response(
            data=_serialize(bank_info),
            message="Bank information updated successfully"
        )
    except Exception as e:
        raise e

@router.get(
    "/vendor/bank-info",
    summary="Get Bank Information",
    description="Retrieves the bank details for the authenticated vendor.",
    response_model=BankInfoAPIResponse,
)
async def get_bank_info(
    token: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine),
):
    """Get bank information for the authenticated vendor."""
    vendor_id = token.get("vendor_id")
    try:
        bank_info = await bank_info_service.get_bank_info(engine=engine, vendor_id=vendor_id)
        return success_response(data=_serialize(bank_info))
    except Exception:
        return success_response(data=None, message="Bank information not found")

@router.delete(
    "/vendor/bank-info",
    summary="Delete Bank Information",
    description="Removes the bank details for the authenticated vendor.",
    response_model=APIResponse,
)
async def delete_bank_info(
    token: dict = Depends(get_current_vendor),
    engine: AIOEngine = Depends(get_engine),
):
    """Delete bank information for the authenticated vendor."""
    vendor_id = token.get("vendor_id")
    success = await bank_info_service.delete_bank_info(engine=engine, vendor_id=vendor_id)
    if not success:
        return success_response(message="Bank information not found or already deleted")
    return success_response(message="Bank information deleted successfully")
