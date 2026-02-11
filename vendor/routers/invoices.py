"""
Invoice Management API Endpoints
Complete CRUD operations with audit trail
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from odmantic import AIOEngine
from typing import Optional

from core.database import get_engine
from core.security import require_vendor
from utils.response import success_response, error_response

from vendor.schemas.invoice import (
    InvoiceGenerateRequest,
    InvoiceCreateManualRequest,
    InvoiceUpdateRequest,
    InvoiceMarkPaidRequest,
    InvoiceCancelRequest,
    InvoiceResendRequest,
    InvoiceResponse,
    InvoiceListResponse,
    InvoiceAuditLogResponse,
    TaxConfigCreate,
    TaxConfigUpdate,
    TaxConfigResponse
)
from vendor.services.invoice_service import (
    generate_invoice_from_booking,
    send_invoice,
    get_vendor_invoices,
    get_invoice_by_id,
    update_invoice,
    mark_invoice_paid,
    cancel_invoice,
    get_invoice_audit_logs,
    create_tax_config,
    get_default_tax_config
)
from vendor.models.invoice import InvoiceTaxConfig
from core.enums import InvoiceStatus
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/vendor/invoices",
    tags=["Vendor - Invoice Management"],
)


# ============================================
# Tax Configuration Endpoints
# ============================================

@router.post("/tax-config")
async def create_tax_configuration(
    payload: TaxConfigCreate,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """
    Create tax configuration for invoices
    
    Allows vendors to configure tax rules (GST, CGST+SGST, IGST, VAT)
    """
    vendor_id = token.get("vendor_id")
    
    try:
        tax_config = await create_tax_config(engine, vendor_id, payload)
        
        return success_response(
            message="Tax configuration created successfully",
            data=TaxConfigResponse(
                id=str(tax_config.id),
                vendor_id=tax_config.vendor_id,
                location_id=tax_config.location_id,
                tax_type=tax_config.tax_type,
                tax_name=tax_config.tax_name,
                tax_percentage=tax_config.tax_percentage,
                cgst_percentage=tax_config.cgst_percentage,
                sgst_percentage=tax_config.sgst_percentage,
                service_charge_percentage=tax_config.service_charge_percentage,
                other_charges=tax_config.other_charges,
                is_active=tax_config.is_active,
                is_default=tax_config.is_default,
                notes=tax_config.notes,
                created_at=tax_config.created_at,
                updated_at=tax_config.updated_at
            ).model_dump()
        ).model_dump()
        
    except Exception as e:
        logger.error(f"Failed to create tax config: {str(e)}")
        return error_response(message=str(e)).model_dump()


@router.get("/tax-config")
async def get_tax_configurations(
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """Get all tax configurations for vendor"""
    vendor_id = token.get("vendor_id")
    
    configs = await engine.find(
        InvoiceTaxConfig,
        InvoiceTaxConfig.vendor_id == vendor_id
    )
    
    return success_response(
        data=[
            TaxConfigResponse(
                id=str(c.id),
                vendor_id=c.vendor_id,
                location_id=c.location_id,
                tax_type=c.tax_type,
                tax_name=c.tax_name,
                tax_percentage=c.tax_percentage,
                cgst_percentage=c.cgst_percentage,
                sgst_percentage=c.sgst_percentage,
                service_charge_percentage=c.service_charge_percentage,
                other_charges=c.other_charges,
                is_active=c.is_active,
                is_default=c.is_default,
                notes=c.notes,
                created_at=c.created_at,
                updated_at=c.updated_at
            ).model_dump()
            for c in configs
        ]
    ).model_dump()


# ============================================
# Invoice Generation
# ============================================

@router.post("/generate")
async def generate_invoice_from_completed_booking(
    payload: InvoiceGenerateRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """
    Auto-generate invoice from completed booking
    
    **Requirements:**
    - Booking must be in COMPLETED status
    - Booking must belong to this vendor
    - Invoice must not already exist for this booking
    
    **Process:**
    1. Validates booking exists and is completed
    2. Fetches vendor and tax configuration
    3. Generates unique invoice number
    4. Calculates all totals with tax breakdown
    5. Creates audit log entry
    6. Optionally sends invoice to customer
    """
    vendor_id = token.get("vendor_id")
    
    try:
        invoice = await generate_invoice_from_booking(
            engine=engine,
            vendor_id=vendor_id,
            booking_id=payload.booking_id,
            due_days=payload.due_days,
            notes=payload.notes,
            terms_and_conditions=payload.terms_and_conditions,
            auto_send=payload.auto_send
        )
        
        return success_response(
            message=f"Invoice generated successfully: {invoice.invoice_number}",
            data=InvoiceResponse(
                id=str(invoice.id),
                vendor_id=invoice.vendor_id,
                customer_id=invoice.customer_id,
                booking_id=invoice.booking_id,
                invoice_number=invoice.invoice_number,
                invoice_date=invoice.invoice_date,
                due_date=invoice.due_date,
                customer_name=invoice.customer_name,
                customer_email=invoice.customer_email,
                customer_phone=invoice.customer_phone,
                customer_address=invoice.customer_address,
                vendor_name=invoice.vendor_name,
                vendor_email=invoice.vendor_email,
                vendor_phone=invoice.vendor_phone,
                vendor_address=invoice.vendor_address,
                vendor_gstin=invoice.vendor_gstin,
                service_name=invoice.service_name,
                service_date=invoice.service_date,
                subtotal=invoice.subtotal,
                discount_amount=invoice.discount_amount,
                discount_percentage=invoice.discount_percentage,
                tax_type=invoice.tax_type,
                tax_amount=invoice.tax_amount,
                cgst_amount=invoice.cgst_amount,
                sgst_amount=invoice.sgst_amount,
                igst_amount=invoice.igst_amount,
                service_charge=invoice.service_charge,
                other_charges=invoice.other_charges,
                total_before_tax=invoice.total_before_tax,
                total_tax=invoice.total_tax,
                grand_total=invoice.grand_total,
                paid_amount=invoice.paid_amount,
                balance_due=invoice.balance_due,
                status=invoice.status,
                sent_at=invoice.sent_at,
                sent_count=invoice.sent_count,
                cancelled_at=invoice.cancelled_at,
                cancellation_reason=invoice.cancellation_reason,
                payment_received_at=invoice.payment_received_at,
                payment_method=invoice.payment_method,
                payment_reference=invoice.payment_reference,
                notes=invoice.notes,
                terms_and_conditions=invoice.terms_and_conditions,
                created_at=invoice.created_at,
                updated_at=invoice.updated_at
            ).model_dump()
        ).model_dump()
        
    except HTTPException as e:
        return error_response(message=e.detail).model_dump()
    except Exception as e:
        logger.error(f"Failed to generate invoice: {str(e)}")
        return error_response(message=f"Failed to generate invoice: {str(e)}").model_dump()


# ============================================
# Get Invoices
# ============================================

@router.get("/")
async def get_all_invoices(
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
    status: Optional[InvoiceStatus] = Query(None, description="Filter by status"),
    customer_id: Optional[str] = Query(None, description="Filter by customer"),
    search: Optional[str] = Query(None, description="Search by Invoice #, Customer Name, or ID"),
    due_date_start: Optional[datetime] = Query(None, description="Filter by due date (start)"),
    due_date_end: Optional[datetime] = Query(None, description="Filter by due date (end)"),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
):
    """
    Get all invoices for vendor with optional filters
    
    **Filters:**
    - status: Filter by invoice status
    - customer_id: Filter by specific customer
    - search: Search by Invoice #, Customer Name, or ID
    - due_date_start/end: Filter by due date range
    - limit: Number of results (default 50, max 100)
    - skip: Skip first N results for pagination
    """
    vendor_id = token.get("vendor_id")
    
    try:
        invoices, total = await get_vendor_invoices(
            engine=engine,
            vendor_id=vendor_id,
            status_filter=status,
            customer_id=customer_id,
            search=search,
            start_date=due_date_start,
            end_date=due_date_end,
            limit=limit,
            skip=skip
        )
        
        return success_response(
            data={
                "data": [
                    InvoiceListResponse(
                        id=str(inv.id),
                        invoice_number=inv.invoice_number,
                        invoice_date=inv.invoice_date,
                        due_date=inv.due_date,
                        customer_name=inv.customer_name,
                        service_name=inv.service_name,
                        grand_total=inv.grand_total,
                        paid_amount=inv.paid_amount,
                        balance_due=inv.balance_due,
                        status=inv.status,
                        sent_count=inv.sent_count,
                        created_at=inv.created_at
                    ).model_dump()
                    for inv in invoices
                ],
                "meta": {
                    "total": total,
                    "skip": skip,
                    "limit": limit
                }
            }
        ).model_dump()
        
    except Exception as e:
        logger.error(f"Failed to get invoices: {str(e)}")
        return error_response(message=str(e)).model_dump()


@router.get("/{invoice_id}")
async def get_invoice_details(
    invoice_id: str,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """Get complete invoice details by ID"""
    vendor_id = token.get("vendor_id")
    
    try:
        invoice = await get_invoice_by_id(engine, vendor_id, invoice_id)
        
        return success_response(
            data=InvoiceResponse(
                id=str(invoice.id),
                vendor_id=invoice.vendor_id,
                customer_id=invoice.customer_id,
                booking_id=invoice.booking_id,
                invoice_number=invoice.invoice_number,
                invoice_date=invoice.invoice_date,
                due_date=invoice.due_date,
                customer_name=invoice.customer_name,
                customer_email=invoice.customer_email,
                customer_phone=invoice.customer_phone,
                customer_address=invoice.customer_address,
                vendor_name=invoice.vendor_name,
                vendor_email=invoice.vendor_email,
                vendor_phone=invoice.vendor_phone,
                vendor_address=invoice.vendor_address,
                vendor_gstin=invoice.vendor_gstin,
                service_name=invoice.service_name,
                service_date=invoice.service_date,
                subtotal=invoice.subtotal,
                discount_amount=invoice.discount_amount,
                discount_percentage=invoice.discount_percentage,
                tax_type=invoice.tax_type,
                tax_amount=invoice.tax_amount,
                cgst_amount=invoice.cgst_amount,
                sgst_amount=invoice.sgst_amount,
                igst_amount=invoice.igst_amount,
                service_charge=invoice.service_charge,
                other_charges=invoice.other_charges,
                total_before_tax=invoice.total_before_tax,
                total_tax=invoice.total_tax,
                grand_total=invoice.grand_total,
                paid_amount=invoice.paid_amount,
                balance_due=invoice.balance_due,
                status=invoice.status,
                sent_at=invoice.sent_at,
                sent_count=invoice.sent_count,
                cancelled_at=invoice.cancelled_at,
                cancellation_reason=invoice.cancellation_reason,
                payment_received_at=invoice.payment_received_at,
                payment_method=invoice.payment_method,
                payment_reference=invoice.payment_reference,
                notes=invoice.notes,
                terms_and_conditions=invoice.terms_and_conditions,
                created_at=invoice.created_at,
                updated_at=invoice.updated_at
            ).model_dump()
        ).model_dump()
        
    except HTTPException as e:
        return error_response(message=e.detail).model_dump()
    except Exception as e:
        logger.error(f"Failed to get invoice: {str(e)}")
        return error_response(message=str(e)).model_dump()


# ============================================
# Update Invoice
# ============================================

@router.patch("/{invoice_id}")
async def update_invoice_details(
    invoice_id: str,
    payload: InvoiceUpdateRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """
    Update invoice details (DRAFT invoices only)
    
    **Can update:**
    - Line items
    - Discounts
    - Due date
    - Notes
    - Terms and conditions
    
    **Cannot update:**
    - Customer/vendor details
    - Invoice number
    - Already sent/paid invoices
    """
    vendor_id = token.get("vendor_id")
    
    try:
        invoice = await update_invoice(engine, vendor_id, invoice_id, payload)
        
        return success_response(
            message="Invoice updated successfully",
            data={"invoice_id": str(invoice.id), "invoice_number": invoice.invoice_number}
        ).model_dump()
        
    except HTTPException as e:
        return error_response(message=e.detail).model_dump()
    except Exception as e:
        logger.error(f"Failed to update invoice: {str(e)}")
        return error_response(message=str(e)).model_dump()


# ============================================
# Send/Resend Invoice
# ============================================

@router.post("/{invoice_id}/send")
async def send_invoice_to_customer(
    invoice_id: str,
    payload: InvoiceResendRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """
    Send or resend invoice to customer
    
    **Sends via:**
    - Email (default)
    - SMS
    - WhatsApp
    
    **Creates audit trail and updates sent count**
    """
    vendor_id = token.get("vendor_id")
    
    try:
        invoice = await send_invoice(
            engine=engine,
            vendor_id=vendor_id,
            invoice_id=invoice_id,
            channels=payload.channels,
            notes=payload.notes
        )
        
        return success_response(
            message=f"Invoice {invoice.invoice_number} sent successfully via {', '.join(payload.channels)}",
            data={"invoice_id": str(invoice.id), "sent_count": invoice.sent_count}
        ).model_dump()
        
    except HTTPException as e:
        return error_response(message=e.detail).model_dump()
    except Exception as e:
        logger.error(f"Failed to send invoice: {str(e)}")
        return error_response(message=str(e)).model_dump()


# ============================================
# Mark as Paid
# ============================================

@router.post("/{invoice_id}/mark-paid")
async def mark_invoice_as_paid(
    invoice_id: str,
    payload: InvoiceMarkPaidRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """
    Mark invoice as paid (full or partial payment)
    
    **Records:**
    - Payment amount
    - Payment method
    - Payment reference/transaction ID
    - Payment date
    
    **Automatically updates status:**
    - PAID (if fully paid)
    - PARTIALLY_PAID (if partial)
    """
    vendor_id = token.get("vendor_id")
    
    try:
        invoice = await mark_invoice_paid(engine, vendor_id, invoice_id, payload)
        
        return success_response(
            message=f"Payment recorded: ₹{payload.paid_amount}. Status: {invoice.status}",
            data={
                "invoice_id": str(invoice.id),
                "invoice_number": invoice.invoice_number,
                "paid_amount": invoice.paid_amount,
                "balance_due": invoice.balance_due,
                "status": invoice.status
            }
        ).model_dump()
        
    except HTTPException as e:
        return error_response(message=e.detail).model_dump()
    except Exception as e:
        logger.error(f"Failed to mark invoice as paid: {str(e)}")
        return error_response(message=str(e)).model_dump()


# ============================================
# Cancel Invoice
# ============================================

@router.post("/{invoice_id}/cancel")
async def cancel_invoice_endpoint(
    invoice_id: str,
    payload: InvoiceCancelRequest,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """
    Cancel invoice with reason
    
    **Cannot cancel:**
    - Already paid invoices
    - Refunded invoices
    - Already cancelled invoices
    
    **Creates full audit trail**
    """
    vendor_id = token.get("vendor_id")
    
    try:
        invoice = await cancel_invoice(engine, vendor_id, invoice_id, payload.reason)
        
        return success_response(
            message=f"Invoice {invoice.invoice_number} cancelled successfully",
            data={"invoice_id": str(invoice.id), "status": invoice.status}
        ).model_dump()
        
    except HTTPException as e:
        return error_response(message=e.detail).model_dump()
    except Exception as e:
        logger.error(f"Failed to cancel invoice: {str(e)}")
        return error_response(message=str(e)).model_dump()


# ============================================
# Audit Logs
# ============================================

@router.get("/{invoice_id}/audit-logs")
async def get_invoice_audit_trail(
    invoice_id: str,
    token: dict = Depends(require_vendor()),
    engine: AIOEngine = Depends(get_engine),
):
    """
    Get complete audit trail for invoice
    
    **Shows all actions:**
    - GENERATED
    - SENT/RESENT
    - EDITED (with field changes)
    - PAYMENT_RECEIVED
    - CANCELLED
    - REFUNDED
    """
    vendor_id = token.get("vendor_id")
    
    try:
        logs = await get_invoice_audit_logs(engine, vendor_id, invoice_id)
        
        return success_response(
            data=[
                InvoiceAuditLogResponse(
                    id=str(log.id),
                    invoice_number=log.invoice_number,
                    action=log.action,
                    performed_by=log.performed_by,
                    performed_by_role=log.performed_by_role,
                    field_changed=log.field_changed,
                    old_value=str(log.old_value) if log.old_value else None,
                    new_value=str(log.new_value) if log.new_value else None,
                    reason=log.reason,
                    notes=log.notes,
                    timestamp=log.timestamp
                ).model_dump()
                for log in logs
            ]
        ).model_dump()
        
    except HTTPException as e:
        return error_response(message=e.detail).model_dump()
    except Exception as e:
        logger.error(f"Failed to get audit logs: {str(e)}")
        return error_response(message=str(e)).model_dump()
