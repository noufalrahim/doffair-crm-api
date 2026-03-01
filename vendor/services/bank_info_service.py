"""
Bank Info Service
CRUD operations for vendor bank information.
"""
from datetime import datetime
from typing import Optional
from odmantic import AIOEngine
from bson import ObjectId
from fastapi import HTTPException, status
import logging

from vendor.models.bank_info import BankInfo

logger = logging.getLogger(__name__)

async def create_or_update_bank_info(
    engine: AIOEngine,
    vendor_id: str,
    bank_name: str,
    account_number: str,
    ifsc_code: str,
    account_holder_name: str,
    branch_name: Optional[str] = None,
) -> BankInfo:
    """Create or update bank information for a vendor."""
    bank_info = await engine.find_one(BankInfo, BankInfo.vendor_id == vendor_id)
    
    if bank_info:
        bank_info.bank_name = bank_name
        bank_info.account_number = account_number
        bank_info.ifsc_code = ifsc_code
        bank_info.account_holder_name = account_holder_name
        bank_info.branch_name = branch_name
        bank_info.updated_at = datetime.utcnow()
        # Reset verification on update
        bank_info.is_verified = False
        await engine.save(bank_info)
        logger.info(f"✅ Bank info updated for vendor {vendor_id}")
    else:
        bank_info = BankInfo(
            vendor_id=vendor_id,
            bank_name=bank_name,
            account_number=account_number,
            ifsc_code=ifsc_code,
            account_holder_name=account_holder_name,
            branch_name=branch_name,
        )
        await engine.save(bank_info)
        logger.info(f"✅ Bank info created for vendor {vendor_id}")
    
    return bank_info

async def update_bank_info_by_id(
    engine: AIOEngine,
    bank_info_id: str,
    vendor_id: str,
    update_data: dict,
) -> BankInfo:
    """Partially update bank information by its ID for a specific vendor."""
    try:
        oid = ObjectId(bank_info_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bank info ID format"
        )

    bank_info = await engine.find_one(
        BankInfo,
        (BankInfo.id == oid) & (BankInfo.vendor_id == vendor_id)
    )
    if not bank_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank information not found"
        )

    for field, value in update_data.items():
        setattr(bank_info, field, value)
    bank_info.updated_at = datetime.utcnow()
    bank_info.is_verified = False
    await engine.save(bank_info)
    logger.info(f"✅ Bank info {bank_info_id} partially updated for vendor {vendor_id}")
    return bank_info

async def get_bank_info(engine: AIOEngine, vendor_id: str) -> BankInfo:
    """Get bank information for a vendor."""
    bank_info = await engine.find_one(BankInfo, BankInfo.vendor_id == vendor_id)
    if not bank_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank information not found"
        )
    return bank_info

async def delete_bank_info(engine: AIOEngine, vendor_id: str) -> bool:
    """Delete bank information for a vendor."""
    bank_info = await engine.find_one(BankInfo, BankInfo.vendor_id == vendor_id)
    if not bank_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank information not found"
        )
    await engine.delete(bank_info)
    logger.info(f"🗑️ Bank info deleted for vendor {vendor_id}")
    return True
