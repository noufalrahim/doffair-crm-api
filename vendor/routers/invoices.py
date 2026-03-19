from fastapi import APIRouter, Depends, Query
from odmantic import AIOEngine
from typing import Optional

from core.database import get_engine
from core.security import require_vendor
from utils.response import success_response, error_response

from vendor.schemas.invoice import (
    InvoiceCreateRequest,
    InvoiceUpdateRequest,
    InvoiceResponse,
    InvoiceListResponse,
    InvoiceItemSchema
)
from vendor.services.invoice_service import (
    create_invoice,
    get_invoice_by_id,
    list_invoices,
    update_invoice,
    delete_invoice,
    get_invoice_statistics
)
from core.enums import InvoiceStatus

router = APIRouter(
    prefix="/vendor/invoices",
    tags=["Vendor - Invoice Management"],
)


def map_invoice_to_response(invoice) -> InvoiceResponse:
    """Helper to map Invoice model to InvoiceResponse schema"""
    return InvoiceResponse(
        id=str(invoice.id),
        invoice_number=invoice.invoice_number,
        invoice_date=invoice.invoice_date,
        due_date=invoice.due_date,
        customer_id=invoice.customer_id,
        booking_id=invoice.booking_id,
        vertical_id=getattr(invoice, 'vertical_id', None),
        items=[InvoiceItemSchema(**item.model_dump()) for item in invoice.items] if hasattr(invoice, 'items') else [],
        notes=getattr(invoice, 'notes', None),
        tax_amount=getattr(invoice, 'tax_amount', 0.0),
        discount_amount=getattr(invoice, 'discount_amount', 0.0),
        grand_total=invoice.grand_total,
        paid_amount=invoice.paid_amount,
        balance_due=invoice.balance_due,
        status=invoice.status,
        created_at=invoice.created_at,
        updated_at=invoice.updated_at
    )


@router.post("")
async def create_new_invoice(
    payload: InvoiceCreateRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """
    Manually create a new invoice
    """
    vendor_id = token.get("vendor_id")
    try:
        invoice = await create_invoice(engine, vendor_id, payload)
        return success_response(
            message="Invoice created successfully",
            data=map_invoice_to_response(invoice).model_dump()
        ).model_dump()
    except Exception as e:
        return error_response(message=str(e)).model_dump()


@router.get("")
async def get_all_invoices(
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
    customer_id: Optional[str] = Query(None),
    status: Optional[InvoiceStatus] = Query(None),
    vertical_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """
    List all invoices with filters
    """
    vendor_id = token.get("vendor_id")
    try:
        invoices, total = await list_invoices(
            engine, vendor_id, customer_id, status, vertical_id, skip, limit
        )
        return success_response(
            data={
                "total": total,
                "invoices": [
                    map_invoice_to_response(inv).model_dump()
                    for inv in invoices
                ]
            }
        ).model_dump()
    except Exception as e:
        return error_response(message=str(e)).model_dump()


@router.get("/{invoice_id}")
async def get_invoice_details(
    invoice_id: str,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """
    Get detailed information about an invoice
    """
    vendor_id = token.get("vendor_id")
    try:
        invoice = await get_invoice_by_id(engine, vendor_id, invoice_id)
        return success_response(
            data=map_invoice_to_response(invoice).model_dump()
        ).model_dump()
    except Exception as e:
        return error_response(message=str(e)).model_dump()


@router.patch("/{invoice_id}")
async def update_invoice_details(
    invoice_id: str,
    payload: InvoiceUpdateRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """
    Update invoice details
    """
    vendor_id = token.get("vendor_id")
    try:
        invoice = await update_invoice(engine, vendor_id, invoice_id, payload)
        return success_response(
            message="Invoice updated successfully",
            data=map_invoice_to_response(invoice).model_dump()
        ).model_dump()
    except Exception as e:
        return error_response(message=str(e)).model_dump()


@router.delete("/{invoice_id}")
async def delete_existing_invoice(
    invoice_id: str,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """
    Delete an invoice
    """
    vendor_id = token.get("vendor_id")
    try:
        await delete_invoice(engine, vendor_id, invoice_id)
        return success_response(message="Invoice deleted successfully").model_dump()
    except Exception as e:
        return error_response(message=str(e)).model_dump()


@router.get("/stats/summary")
async def get_invoice_stats(
    vertical_id: Optional[str] = Query(None),
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """
    Get financial statistics for the vendor
    """
    vendor_id = token.get("vendor_id")
    try:
        stats = await get_invoice_statistics(engine, vendor_id, vertical_id)
        return success_response(
            data=stats.model_dump()
        ).model_dump()
    except Exception as e:
        return error_response(message=str(e)).model_dump()
