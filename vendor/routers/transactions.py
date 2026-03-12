from fastapi import APIRouter, Depends, Query, HTTPException
from odmantic import AIOEngine
from typing import Optional

from core.database import get_engine
from core.security import require_vendor
from utils.response import success_response, error_response

from vendor.schemas.transaction import (
    TransactionCreateRequest,
    TransactionUpdateRequest,
    TransactionResponse,
    TransactionListResponse
)
from vendor.services.transaction_service import (
    create_transaction,
    update_transaction,
    list_transactions,
    delete_transaction
)
from core.enums import TransactionStatus

router = APIRouter(
    prefix="/vendor/transactions",
    tags=["Vendor - Transaction Management"],
)


@router.post("")
async def create_new_transaction(
    payload: TransactionCreateRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """Create a new transaction for an invoice"""
    vendor_id = token.get("vendor_id")
    try:
        transaction = await create_transaction(engine, vendor_id, payload)
        return success_response(
            message="Transaction created successfully",
            data=TransactionResponse(
                id=str(transaction.id),
                vendor_id=transaction.vendor_id,
                invoice_id=transaction.invoice_id,
                booking_id=transaction.booking_id,
                customer_id=transaction.customer_id,
                amount=transaction.amount,
                status=transaction.status,
                date=transaction.date,
                time=transaction.time,
                created_at=transaction.created_at,
                updated_at=transaction.updated_at
            ).model_dump()
        ).model_dump()
    except Exception as e:
        return error_response(message=str(e)).model_dump()


@router.get("")
async def get_all_transactions(
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
    invoice_id: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    status: Optional[TransactionStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """List transactions with filters"""
    vendor_id = token.get("vendor_id")
    try:
        transactions, total = await list_transactions(
            engine, vendor_id, invoice_id, customer_id, status, skip, limit
        )
        return success_response(
            data={
                "total": total,
                "transactions": [
                    TransactionResponse(
                        id=str(t.id),
                        vendor_id=t.vendor_id,
                        invoice_id=t.invoice_id,
                        booking_id=t.booking_id,
                        customer_id=t.customer_id,
                        amount=t.amount,
                        status=t.status,
                        date=t.date,
                        time=t.time,
                        created_at=t.created_at,
                        updated_at=t.updated_at
                    ).model_dump()
                    for t in transactions
                ]
            }
        ).model_dump()
    except Exception as e:
        return error_response(message=str(e)).model_dump()


@router.patch("/{transaction_id}")
async def update_transaction_details(
    transaction_id: str,
    payload: TransactionUpdateRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """Update transaction status or amount"""
    vendor_id = token.get("vendor_id")
    try:
        transaction = await update_transaction(engine, vendor_id, transaction_id, payload)
        return success_response(
            message="Transaction updated successfully",
            data=TransactionResponse(
                id=str(transaction.id),
                vendor_id=transaction.vendor_id,
                invoice_id=transaction.invoice_id,
                booking_id=transaction.booking_id,
                customer_id=transaction.customer_id,
                amount=transaction.amount,
                status=transaction.status,
                date=transaction.date,
                time=transaction.time,
                created_at=transaction.created_at,
                updated_at=transaction.updated_at
            ).model_dump()
        ).model_dump()
    except HTTPException as e:
        return error_response(message=e.detail).model_dump()
    except Exception as e:
        return error_response(message=str(e)).model_dump()


@router.delete("/{transaction_id}")
async def delete_existing_transaction(
    transaction_id: str,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """Delete a transaction"""
    vendor_id = token.get("vendor_id")
    try:
        await delete_transaction(engine, vendor_id, transaction_id)
        return success_response(message="Transaction deleted successfully").model_dump()
    except HTTPException as e:
        return error_response(message=e.detail).model_dump()
    except Exception as e:
        return error_response(message=str(e)).model_dump()
