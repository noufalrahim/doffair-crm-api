import random
import string
from datetime import datetime
from typing import Optional, List, Tuple, Any
from odmantic import AIOEngine
from bson import ObjectId, DBRef
from fastapi import HTTPException, status, BackgroundTasks
import logging

from vendor.models.invoice import Invoice, InvoiceItem
from user.models.booking import Booking
from vendor.models.vendor import Vendor
from vendor.models.vendor_location import VendorLocation
from user.models.user import User
from vendor.schemas.invoice import (
    InvoiceCreateRequest, 
    InvoiceUpdateRequest,
    InvoiceStatisticsResponse,
    InvoiceItemSchema,
    InvoiceGenerateRequest,
    InvoiceSendRequest
)
from vendor.schemas.transaction import TransactionCreateRequest
from core.enums import InvoiceStatus, TransactionStatus
from core.database import get_secondary_engine
from vendor.services.transaction_service import create_transaction
from notifications.events.publisher import event_publisher
from notifications.events.types import EventType, EventSource

logger = logging.getLogger(__name__)

async def calculate_invoice_totals(items: List[InvoiceItem], tax_amount_input: float = 0.0, discount_amount_input: float = 0.0) -> dict:
    """
    Calculate taxable value, tax breakdown, and rounding off.
    Matches the logic in the sample PDF.
    """
    tax_details = {}
    total_tax_amount = 0.0
    total_taxable_value = 0.0
    total_amount = 0.0
    total_mrp = 0.0

    for item in items:
        # If tax_rate is provided but tax_amount is not, calculate it
        if item.tax_rate > 0 and item.tax_amount == 0:
            item.taxable_value = item.unit_price * item.quantity
            item.tax_amount = round(item.taxable_value * (item.tax_rate / 100), 2)
        
        item.subtotal = item.taxable_value + item.tax_amount
        
        total_taxable_value += item.taxable_value
        total_tax_amount += item.tax_amount
        total_amount += item.subtotal
        total_mrp += (item.mrp or 0.0) * item.quantity

        # Tax breakdown (SGST/CGST)
        if item.tax_rate > 0:
            half_rate = item.tax_rate / 2
            half_tax = item.tax_amount / 2
            
            sgst_key = f"sgst {half_rate}%"
            cgst_key = f"cgst {half_rate}%"
            
            tax_details[sgst_key] = tax_details.get(sgst_key, 0.0) + half_tax
            tax_details[cgst_key] = tax_details.get(cgst_key, 0.0) + half_tax

    # Final adjustments
    grand_total_raw = total_amount + tax_amount_input - discount_amount_input
    grand_total = round(grand_total_raw)
    rounding_off = round(grand_total - grand_total_raw, 2)

    return {
        "tax_amount": round(total_tax_amount + tax_amount_input, 2),
        "total_taxable_value": round(total_taxable_value, 2),
        "total_mrp": round(total_mrp, 2),
        "grand_total": float(grand_total),
        "rounding_off": rounding_off,
        "tax_details": {k: round(v, 2) for k, v in tax_details.items()}
    }


def num_to_words(n: float) -> str:
    """Convert number to words in Indian currency format"""
    units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    
    def convert_less_than_thousand(num):
        res = ""
        if num >= 100:
            res += units[num // 100] + " Hundred "
            num %= 100
        if num >= 20:
            res += tens[num // 10] + " "
            num %= 10
        elif num >= 10:
            res += teens[num - 10] + " "
            num = 0
        if num > 0:
            res += units[num] + " "
        return res

    n_int = int(n)
    if n_int == 0: return "Zero Rupees Only"
    
    res = ""
    # Crores
    if n_int >= 10000000:
        res += convert_less_than_thousand(n_int // 10000000) + "Crore "
        n_int %= 10000000
    # Lakhs
    if n_int >= 100000:
        res += convert_less_than_thousand(n_int // 100000) + "Lakh "
        n_int %= 100000
    # Thousands
    if n_int >= 1000:
        res += convert_less_than_thousand(n_int // 1000) + "Thousand "
        n_int %= 1000
    # Rest
    res += convert_less_than_thousand(n_int)
    
    return res.strip().upper() + " RUPEES ONLY"


async def generate_unique_invoice_number(engine: AIOEngine, vendor_id: str) -> str:
    """
    Generate a unique invoice number.
    Format: INV-YYYY-RANDOM (e.g., INV-2024-A7B2)
    """
    year = datetime.utcnow().year
    
    while True:
        # Generate a random 4-char suffix to ensure global uniqueness and maintain some pattern
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        invoice_number = f"INV-{year}-{suffix}"
        
        # Check if exists
        exists = await engine.find_one(Invoice, Invoice.invoice_number == invoice_number)
        if not exists:
            return invoice_number


async def create_invoice(
    engine: AIOEngine, 
    vendor_id: str, 
    payload: InvoiceCreateRequest,
    background_tasks: Optional[BackgroundTasks] = None
) -> Invoice:
    """Create a new itemized invoice with detailed data population"""
    invoice_number = await generate_unique_invoice_number(engine, vendor_id)
    
    # Fetch Vendor and Booking data
    vendor = await engine.find_one(Vendor, Vendor.id == ObjectId(vendor_id))
    booking = None
    location = None
    if payload.booking_id:
        try:
            booking = await engine.find_one(Booking, Booking.id == ObjectId(payload.booking_id))
            if booking and booking.location_id:
                location = await engine.find_one(VendorLocation, VendorLocation.id == ObjectId(booking.location_id))
        except Exception:
            pass

    # Resolve Customer ID and Fetch User data
    customer_id = booking.user_id if booking else payload.customer_id
    print(f"[INVOICE DEBUG] customer_id resolved to: '{customer_id}'")
    
    user = None
    if customer_id:
        try:
            # Users live in secondary DB (doffair_dev)
            user_engine = get_secondary_engine()
            user_col = user_engine.database.get_collection("users")
            user_info_col = user_engine.database.get_collection("userInfo")
            
            
            uid = ObjectId(customer_id) if ObjectId.is_valid(customer_id) else customer_id
            
            raw_user = await user_col.find_one({"_id": uid})
            
            if raw_user:
                # Get User info
                user_info = await user_info_col.find_one({"userId": DBRef("users", uid)})
                if not user_info:
                    user_info = await user_info_col.find_one({"userId": uid})
                
                class _U:
                    pass
                u = _U()
                
                if user_info and user_info.get("name"):
                    u.name = user_info.get("name")
                else:
                    u.name = raw_user.get("username") or raw_user.get("firstName") or "Customer"
                
                u.email = raw_user.get("email", "")
                u.phone = raw_user.get("phoneNumber") or raw_user.get("phone", "")
                
                user = u
                
            print(f"[INVOICE DEBUG] User lookup result: {'FOUND' if user else 'NOT FOUND'} | email='{user.email if user else ''}' | phone='{user.phone if user else ''}' | name='{user.name if user else ''}'")
        except Exception as ue:
            print(f"[INVOICE DEBUG] User lookup failed: {ue}")
    
    invoice_items = []
    if not payload.items and booking:
        # Auto-generate item from booking if no items provided
        invoice_items.append(InvoiceItem(
            name=booking.service_name,
            quantity=1,
            unit_price=booking.base_amount - booking.discount_amount,
            mrp=booking.base_amount,
            taxable_value=booking.base_amount - booking.discount_amount,
            tax_rate=18.0, # Defaulting to 18% as per sample
        ))
    else:
        for item in payload.items:
            invoice_items.append(InvoiceItem(
                name=item.name,
                hsn_sac=item.hsn_sac,
                mrp=item.mrp or item.unit_price,
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount_amount=item.discount_amount,
                taxable_value=item.taxable_value or (item.unit_price * item.quantity),
                tax_rate=item.tax_rate,
                tax_amount=item.tax_amount
            ))
        
    # Calculate totals
    totals = await calculate_invoice_totals(
        invoice_items, 
        payload.tax_amount, 
        payload.discount_amount
    )
    
    # Use payload grand_total if provided (manual override), otherwise use calculated
    grand_total = payload.grand_total if payload.grand_total is not None else totals["grand_total"]
            
    # Map vendor address
    vendor_address = ""
    if location:
        vendor_address = f"{location.address_line_1}, {location.address_line_2 or ''}, {location.city}, {location.state} - {location.pincode}"
    
    invoice = Invoice(
        vendor_id=vendor_id,
        customer_id=customer_id,
        booking_id=payload.booking_id,
        vertical_id=payload.vertical_id or (booking.vertical_id if booking else None),
        invoice_number=invoice_number,
        due_date=payload.due_date,
        
        # Cached details
        vendor_name=vendor.legal_name if vendor else "Vendor",
        vendor_address=vendor_address,
        vendor_gstin=vendor.gst_number if vendor else None,
        vendor_phone=vendor.primary_contact_phone if vendor else None,
        
        customer_name=user.name if user else (booking.user_name if booking else "Customer"),
        customer_phone=user.phone if user else (booking.user_phone if booking else ""),
        customer_pincode=booking.service_pincode if booking else None,
        
        items=invoice_items,
        notes=payload.notes,
        tax_amount=totals["tax_amount"],
        discount_amount=payload.discount_amount,
        rounding_off=totals["rounding_off"],
        grand_total=grand_total,
        grand_total_words=num_to_words(grand_total),
        paid_amount=0.0,
        balance_due=grand_total,
        tax_details=totals["tax_details"],
        status=InvoiceStatus.DRAFT
    )
    
    await engine.save(invoice)
    logger.info(f"✅ Itemized Invoice created: {invoice_number}")
    
    # Send invoice via email immediately on creation
    try:
        # Resolve email — prioritize live DB user, then booking cache
        resolved_email = (user.email if user else None) or (booking.user_email if booking else None) or ""
        resolved_phone = (user.phone if user else None) or (booking.user_phone if booking else None) or ""
        resolved_name = (user.name if user else None) or (booking.user_name if booking else None) or "Customer"
        print(f"[INVOICE] 📧 Triggering email for invoice {invoice_number}")
        print(f"[INVOICE]    → To: {resolved_email} | Phone: {resolved_phone} | Name: {resolved_name}")
        
        event_data = await build_invoice_event_payload(engine, invoice, resolved_name, resolved_phone, resolved_email)

        if background_tasks:
            background_tasks.add_task(
                _publish_invoice_event_sync,
                EventType.INVOICE_SENT,
                invoice_number,
                event_data
            )
        else:
            event_publisher.publish(
                event_type=EventType.INVOICE_SENT,
                source=EventSource.VENDOR_SERVICE,
                data=event_data
            )
        print(f"[INVOICE] ✅ Invoice email event {'offloaded' if background_tasks else 'published'} for {invoice_number}")
    except Exception as e:
        print(f"[INVOICE] ❌ Failed to send invoice email: {str(e)}")
        logger.error(f"❌ Failed to publish invoice email event: {str(e)}")
    
    return invoice


async def get_invoice_by_id(engine: AIOEngine, vendor_id: str, invoice_id: str) -> Invoice:
    """Get an invoice by ID"""
    try:
        invoice = await engine.find_one(
            Invoice, 
            (Invoice.id == ObjectId(invoice_id)) & (Invoice.vendor_id == vendor_id)
        )
    except Exception:
        invoice = None
        
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    return invoice


async def list_invoices(
    engine: AIOEngine,
    vendor_id: str,
    customer_id: Optional[str] = None,
    status: Optional[InvoiceStatus] = None,
    vertical_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
) -> Tuple[List[Invoice], int]:
    """List invoices with filters"""
    query = [Invoice.vendor_id == vendor_id]
    
    if customer_id:
        query.append(Invoice.customer_id == customer_id)
    if status:
        query.append(Invoice.status == status)
    if vertical_id:
        query.append(Invoice.vertical_id == vertical_id)
        
    invoices = await engine.find(
        Invoice,
        *query,
        sort=Invoice.created_at.desc(),
        skip=skip,
        limit=limit
    )
    total = await engine.count(Invoice, *query)
    
    return invoices, total


async def update_invoice(
    engine: AIOEngine, 
    vendor_id: str, 
    invoice_id: str, 
    payload: InvoiceUpdateRequest,
    background_tasks: Optional[BackgroundTasks] = None
) -> Invoice:
    """Update an invoice and recalculate balance_due if needed"""
    invoice = await get_invoice_by_id(engine, vendor_id, invoice_id)
    
    update_data = payload.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(invoice, key, value)
        
    # Recalculate balance due
    invoice.balance_due = max(0.0, invoice.grand_total - invoice.paid_amount)
    
    # Auto-update status to PAID if balance is 0 and it was previously partially paid or sent
    if invoice.balance_due == 0 and invoice.status in [InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID]:
        invoice.status = InvoiceStatus.PAID
        
    invoice.updated_at = datetime.utcnow()
    await engine.save(invoice)
    
    if invoice.status == InvoiceStatus.SENT:
        # Trigger Notification
        # We need to fetch the customer/user to get their phone/email if not in payload
        user_engine = get_secondary_engine()
        user_col = user_engine.database.get_collection("users")
        user_info_col = user_engine.database.get_collection("userInfo")
        
        
        uid = ObjectId(invoice.customer_id) if ObjectId.is_valid(invoice.customer_id) else invoice.customer_id
        
        raw_user = await user_col.find_one({"_id": uid}) if invoice.customer_id else None
        class _U:
            pass
        user = None
        if raw_user:
            user = _U()
            user.email = raw_user.get("email", "")
            user.phone = raw_user.get("phoneNumber") or raw_user.get("phone", "")
            
            user_info = await user_info_col.find_one({"userId": DBRef("users", uid)})
            if not user_info:
                user_info = await user_info_col.find_one({"userId": uid})
                
            if user_info and user_info.get("name"):
                user.name = user_info.get("name")
            else:
                user.name = raw_user.get("name") or raw_user.get("username") or raw_user.get("firstName", "Customer")
        
        # Fetch vendor for data enrichment
        vendor = await engine.find_one(Vendor, Vendor.id == ObjectId(invoice.vendor_id))
        
        event_data = await build_invoice_event_payload(engine, invoice, user.name if user else "Customer", user.phone if user else "", user.email if user else "")

        if background_tasks:
            background_tasks.add_task(
                _publish_invoice_event_sync,
                EventType.INVOICE_SENT,
                invoice.invoice_number,
                event_data
            )
        else:
            event_publisher.publish(
                event_type=EventType.INVOICE_SENT,
                source=EventSource.VENDOR_SERVICE,
                data=event_data
            )

    logger.info(f"✏️ Invoice updated: {invoice.invoice_number}")
    return invoice


async def delete_invoice(engine: AIOEngine, vendor_id: str, invoice_id: str) -> bool:
    """Hard delete an invoice"""
    invoice = await get_invoice_by_id(engine, vendor_id, invoice_id)
    await engine.delete(invoice)
    logger.info(f"🗑️ Invoice deleted: {invoice.invoice_number}")
    return True


async def get_invoice_statistics(
    engine: AIOEngine, 
    vendor_id: str, 
    vertical_id: Optional[str] = None
) -> InvoiceStatisticsResponse:
    """
    Get financial statistics for a vendor, optionally filtered by vertical
    """
    query = [Invoice.vendor_id == vendor_id]
    if vertical_id:
        query.append(Invoice.vertical_id == vertical_id)
        
    invoices = await engine.find(Invoice, *query)
    
    stats = {
        "total_earnings": sum(inv.paid_amount for inv in invoices),
        "total_bookings": len(set(inv.booking_id for inv in invoices if inv.booking_id)),
        "total_generated": sum(1 for inv in invoices if inv.status == InvoiceStatus.GENERATED),
        "total_paid": sum(1 for inv in invoices if inv.status == InvoiceStatus.PAID),
        "total_refunded": sum(1 for inv in invoices if inv.status == InvoiceStatus.REFUNDED),
        "total_overdue": sum(1 for inv in invoices if inv.status == InvoiceStatus.OVERDUE)
    }
    
    return InvoiceStatisticsResponse(**stats)


async def generate_invoice_from_booking(
    engine: AIOEngine, 
    vendor_id: str, 
    payload: InvoiceGenerateRequest
) -> Invoice:
    """
    Generate an invoice automatically from a completed booking.
    """
    from datetime import timedelta
    # 1. Fetch booking (Check provided engine, then secondary if not found)
    booking = await engine.find_one(Booking, Booking.id == ObjectId(payload.booking_id))
    
    if not booking:
        try:
            # Check secondary engine (doffair_dev)
            secondary_engine = get_secondary_engine()
            # Try raw collection find because Booking model is tied to 'walkin_bookings' in primary
            # while online bookings are in 'bookings' in secondary
            booking_coll = secondary_engine.database.get_collection("bookings")
            print(f"[INVOICE] Checking secondary DB 'bookings' collection for {payload.booking_id}")
            
            raw_doc = await booking_coll.find_one({"_id": ObjectId(payload.booking_id)})
            if not raw_doc:
                # Also check 'walkin_bookings' in secondary just in case
                raw_doc = await secondary_engine.database.get_collection("walkin_bookings").find_one({"_id": ObjectId(payload.booking_id)})
            
            if raw_doc:
                print(f"[INVOICE] Found booking in secondary DB. Mapping to model...")
                # Basic mapping for legacy/online fields to satisfy Booking model
                if "userId" in raw_doc and "user_id" not in raw_doc:
                    raw_doc["user_id"] = str(raw_doc["userId"])
                if "serviceProviderId" in raw_doc and "vendor_id" not in raw_doc:
                    raw_doc["vendor_id"] = str(raw_doc["serviceProviderId"])
                if "startTime" in raw_doc and "booking_date" not in raw_doc:
                    raw_doc["booking_date"] = raw_doc["startTime"]
                if "bookingAmount" in raw_doc and "final_amount" not in raw_doc:
                    raw_doc["final_amount"] = float(raw_doc["bookingAmount"])
                if "base_amount" not in raw_doc:
                    raw_doc["base_amount"] = float(raw_doc.get("bookingAmount", 0))
                if "serviceType" in raw_doc and "vertical_name" not in raw_doc:
                    raw_doc["vertical_name"] = raw_doc["serviceType"]
                
                # Check for nested services if it's a list
                if not raw_doc.get("service_name") and raw_doc.get("services") and len(raw_doc["services"]) > 0:
                    raw_doc["service_name"] = raw_doc["services"][0].get("name", "Service")

                # Validate into model
                booking = Booking.model_validate(raw_doc)
        except Exception as e:
            print(f"[INVOICE] Error during secondary booking lookup: {e}")
            pass
            
    if not booking:
        raise HTTPException(status_code=404, detail=f"Booking {payload.booking_id} not found across databases")
        
    # Ownership was already verified at the router layer.
    # Log a warning if there is a mismatch (can happen with secondary-DB bookings
    # where vendor_id is mapped from serviceProviderId and may differ in format).
    actual_vendor_id = str(booking.vendor_id).strip() if booking.vendor_id else ""
    if actual_vendor_id and actual_vendor_id != vendor_id.strip():
        logger.warning(
            f"[INVOICE] vendor_id mismatch: booking='{actual_vendor_id}' vs request='{vendor_id}'. "
            f"Proceeding — ownership already confirmed at router level."
        )



    # 2. Prepare Create Request
    # Use booking service name and price for the line item
    item = InvoiceItemSchema(
        name=booking.service_name,
        quantity=1,
        unit_price=booking.base_amount - booking.discount_amount,
        mrp=booking.base_amount,
        taxable_value=booking.base_amount - booking.discount_amount,
        tax_rate=18.0 # Default
    )
    
    # Calculate due date if due_days provided
    due_date = None
    if payload.due_days:
        due_date = datetime.utcnow() + timedelta(days=payload.due_days)

    create_payload = InvoiceCreateRequest(
        customer_id=str(booking.user_id),
        booking_id=payload.booking_id,
        vertical_id=booking.vertical_id,
        due_date=due_date,
        items=[item],
        notes=payload.notes or f"Generated for booking {booking.booking_id}",
        tax_amount=0.0,
        discount_amount=0.0
    )
    
    # 3. Create the invoice
    invoice = await create_invoice(engine, vendor_id, create_payload)
    
    # 4. Handle Transactions (Online vs Walk-in)
    is_offline = True
    payment_reference = None
    
    # Check if this booking came from secondary/online DB
    try:
        if get_secondary_engine():
            online_doc = await get_secondary_engine().database.get_collection("bookings").find_one({"_id": ObjectId(payload.booking_id)})
            if online_doc:
                is_offline = False
                payment_reference = online_doc.get("paymentId")
    except Exception:
        pass

    import traceback
    try:
        from vendor.models.transaction import TransactionStatus
        from vendor.schemas.transaction import TransactionCreateRequest
        from vendor.services.transaction_service import create_transaction
        
        if not is_offline:
            # ONLINE: Auto-generate full transaction
            tx_payload = TransactionCreateRequest(
                invoice_id=str(invoice.id),
                booking_id=payload.booking_id,
                customer_id=str(booking.user_id),
                amount=invoice.grand_total,
                status=TransactionStatus.PAID,
                payment_method="ONLINE",
                payment_reference=payment_reference,
                notes="Auto-recorded: online payment upon invoice generation",
            )
            await create_transaction(engine, vendor_id, tx_payload)
            print(f"[INVOICE] 💰 Auto-recorded full transaction for online booking {payload.booking_id}")
            
        else:
            # WALK-IN: Use payment fields from InvoiceGenerateRequest (amount_paid, etc)
            if payload.amount_paid and payload.amount_paid > 0:
                tx_payload = TransactionCreateRequest(
                    invoice_id=str(invoice.id),
                    booking_id=payload.booking_id,
                    customer_id=str(booking.user_id),
                    amount=payload.amount_paid,
                    status=TransactionStatus.PAID,
                    payment_method=payload.payment_method or "CASH",
                    payment_reference=payload.payment_reference,
                    notes=payload.payment_notes,
                )
                await create_transaction(engine, vendor_id, tx_payload)
                print(f"[INVOICE] 💰 Recorded transaction for walk-in booking {payload.booking_id}")

    except Exception as e:
        print(f"[INVOICE] ❌ Failed to record transaction during generation: {e}")
        traceback.print_exc()

    # Need to reload invoice to reflect paid amount updates from create_transaction
    invoice = await get_invoice_by_id(engine, vendor_id, str(invoice.id))
    
    # 5. Auto-send if requested
    if payload.auto_send:
        invoice.status = InvoiceStatus.SENT
        await engine.save(invoice)
        
    return invoice


def _extract_fields_from_booking_doc(booking_doc: dict) -> dict:
    """
    Normalize a raw MongoDB booking document (works for both primary walkin_bookings
    and secondary online bookings) into a consistent dict for invoice creation.
    """
    # --- Customer ---
    customer_id = (
        str(booking_doc.get("user_id") or "")
        or str(booking_doc.get("userId") or "")
        or str(booking_doc.get("customer_id") or "")
    )

    # --- Service name ---
    service_name = booking_doc.get("service_name") or ""
    if not service_name:
        services = booking_doc.get("services") or []
        if services and isinstance(services[0], dict):
            service_name = services[0].get("name", "")
    if not service_name:
        service_name = (
            booking_doc.get("serviceType")
            or booking_doc.get("vertical_name")
            or "Service"
        )

    # --- Amount ---
    base_amount = float(
        booking_doc.get("base_amount")
        or booking_doc.get("bookingAmount")
        or booking_doc.get("final_amount")
        or booking_doc.get("price")
        or 0
    )
    discount_amount = float(booking_doc.get("discount_amount") or 0)

    # --- Vertical ---
    vertical_id = (
        str(booking_doc.get("vertical_id") or "")
        or str(booking_doc.get("verticalId") or "")
    ) or None

    # --- Payment reference (online bookings) ---
    payment_id = (
        str(booking_doc.get("payment_id") or "")
        or str(booking_doc.get("transactionId") or "")
        or str(booking_doc.get("paymentId") or "")
    ) or None

    return {
        "customer_id": customer_id,
        "service_name": service_name,
        "base_amount": base_amount,
        "discount_amount": discount_amount,
        "vertical_id": vertical_id,
        "payment_id": payment_id,
    }



async def build_invoice_event_payload(engine, invoice, user_name, user_phone, user_email, channels=["in-app", "email"]):
    # Fetch vendor
    from vendor.models.vendor import Vendor
    from bson import ObjectId
    vendor = await engine.find_one(Vendor, Vendor.id == ObjectId(invoice.vendor_id))
    
    # Fetch Location
    from vendor.models.vendor_location import VendorLocation
    location = await engine.find_one(VendorLocation, VendorLocation.vendor_id == invoice.vendor_id, VendorLocation.is_default == True)
    if not location:
        location = await engine.find_one(VendorLocation, VendorLocation.vendor_id == invoice.vendor_id)
        
    store_logo = vendor.logo_blob_path if vendor and getattr(vendor, 'logo_blob_path', None) else ""
    legal_name = vendor.legal_name if vendor and getattr(vendor, 'legal_name', None) else "Doffair Vendor"
    store_name = location.name if location else legal_name
    
    store_address = ""
    if location:
        parts = [location.address_line_1]
        if getattr(location, 'address_line_2', None): parts.append(location.address_line_2)
        parts.append(f"{location.city}, {location.state} {location.pincode}")
        store_address = ", ".join(parts)
    elif vendor and hasattr(vendor, 'about'):
        store_address = "India"
        
    vendor_state = location.state if location else "State"
    
    # Generate words
    try:
        from vendor.services.invoice_service import num_to_words
        words = num_to_words(invoice.grand_total)
    except:
        words = getattr(invoice, 'grand_total_words', "") or ""

    return {
        "invoice_id": str(invoice.id),
        "invoice_number": invoice.invoice_number,
        "invoice_date": invoice.invoice_date.strftime("%Y-%m-%d"),
        "invoice_time": invoice.invoice_date.strftime("%I:%M %p"),
        "vendor_id": invoice.vendor_id,
        "customer_id": invoice.customer_id,
        "user_id": invoice.customer_id,
        "customer_name": user_name,
        "user_name": user_name,
        "user_phone": user_phone,
        "user_email": user_email,
        "customer_pincode": getattr(invoice, 'customer_pincode', "") or "",
        "grand_total": f"{invoice.grand_total:,.2f}",
        "raw_grand_total": invoice.grand_total,
        "balance_due": f"{invoice.balance_due:,.2f}",
        "due_date": invoice.due_date.strftime("%Y-%m-%d") if getattr(invoice, 'due_date', None) else "N/A",
        "service_name": invoice.items[0].name if getattr(invoice, 'items', None) else "Service",
        "service_date": invoice.invoice_date.strftime("%Y-%m-%d"),
        
        "store_logo": store_logo,
        "store_name": store_name,
        "legal_name": legal_name,
        "store_address": store_address,
        "vendor_state": vendor_state,
        
        "vendor_name": vendor.legal_name if vendor else "Doffair Vendor",
        "vendor_phone": vendor.primary_contact_phone if vendor else "",
        "vendor_email": getattr(vendor, 'primary_contact_email', getattr(vendor, 'email', "")),
        "vendor_gstin": getattr(vendor, 'gst_number', ""),
        
        "items": [item.model_dump() for item in invoice.items] if getattr(invoice, 'items', None) else [],
        "tax_details": getattr(invoice, 'tax_details', {}),
        "tax_amount": getattr(invoice, 'tax_amount', 0.0),
        "rounding_off": getattr(invoice, 'rounding_off', 0.0),
        "grand_total_words": words,
        
        "channels": channels,
        "template_id": "InvoiceSent"
    }


async def handle_booking_completion_invoicing(
    engine: AIOEngine,
    vendor_id: str,
    booking_doc: dict,
    status_update: Optional[Any] = None,
) -> Optional[Invoice]:
    """
    Handles automated invoicing and transaction creation when a booking is completed.
    Called as a BackgroundTask — runs after the HTTP response is already sent.

    Works directly from the raw booking_doc dict to avoid ODMantic model validation
    failures caused by schema differences between primary (walkin) and secondary (online) DBs.
    """
    import traceback
    from datetime import timedelta

    try:
        booking_id = str(booking_doc.get("_id") or booking_doc.get("id") or "")
        is_offline = bool(booking_doc.get("is_offline", False))

        logger.info(f"🧾 [INVOICING] Starting for booking={booking_id} | offline={is_offline} | vendor={vendor_id}")

        # --- Extract fields from raw doc (handles both DB schemas) ---
        fields = _extract_fields_from_booking_doc(booking_doc)
        customer_id = fields["customer_id"]
        service_name = fields["service_name"]
        base_amount = fields["base_amount"]
        discount_amount = fields["discount_amount"]
        vertical_id = fields["vertical_id"]

        if not customer_id:
            logger.error(f"[INVOICING] Cannot create invoice: customer_id missing in booking_doc {booking_id}")
            return None

        if base_amount <= 0:
            logger.warning(f"[INVOICING] booking {booking_id} has base_amount={base_amount}. Proceeding with 0.")

        # --- Build invoice line item ---
        taxable_value = max(0.0, base_amount - discount_amount)
        tax_rate = 18.0
        tax_amount = round(taxable_value * (tax_rate / 100), 2)
        item = InvoiceItemSchema(
            name=service_name,
            quantity=1,
            mrp=base_amount,
            unit_price=taxable_value,
            discount_amount=discount_amount,
            taxable_value=taxable_value,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            subtotal=round(taxable_value + tax_amount, 2),
        )

        # --- Build InvoiceCreateRequest ---
        due_date = datetime.utcnow() + timedelta(days=30)
        create_payload = InvoiceCreateRequest(
            customer_id=customer_id,
            booking_id=booking_id,
            vertical_id=vertical_id,
            due_date=due_date,
            items=[item],
            notes="Automatically generated on service completion",
            tax_amount=0.0,
            discount_amount=discount_amount,
        )

        # --- Create invoice (handles user lookup + email notification internally) ---
        invoice = await create_invoice(engine, vendor_id, create_payload)

        # Mark as SENT immediately
        invoice.status = InvoiceStatus.SENT
        await engine.save(invoice)

        logger.info(f"✅ [INVOICING] Invoice created: {invoice.invoice_number} | id={invoice.id} | total={invoice.grand_total}")

        # --- Record transaction ---
        if not is_offline:
            # ONLINE: Full payment assumed via gateway
            tx_payload = TransactionCreateRequest(
                invoice_id=str(invoice.id),
                booking_id=booking_id,
                customer_id=customer_id,
                amount=invoice.grand_total,
                status=TransactionStatus.PAID,
                payment_method="ONLINE",
                payment_reference=fields["payment_id"],
                notes="Auto-recorded: online payment on booking completion",
                date=datetime.utcnow().strftime("%Y-%m-%d"),
                time=datetime.utcnow().strftime("%H:%M:%S"),
            )
            await create_transaction(engine, vendor_id, tx_payload)
            logger.info(f"💰 [INVOICING] ONLINE transaction: ₹{invoice.grand_total} for {booking_id}")

        else:
            # WALK-IN: Use vendor-supplied payment details
            amount_paid = getattr(status_update, "amount_paid", None) if status_update else None
            payment_method = getattr(status_update, "payment_method", None) if status_update else None
            payment_reference = getattr(status_update, "payment_reference", None) if status_update else None
            payment_notes = getattr(status_update, "payment_notes", None) if status_update else None

            if amount_paid and amount_paid > 0:
                tx_payload = TransactionCreateRequest(
                    invoice_id=str(invoice.id),
                    booking_id=booking_id,
                    customer_id=customer_id,
                    amount=amount_paid,
                    status=TransactionStatus.PAID,
                    payment_method=payment_method or "CASH",
                    payment_reference=payment_reference,
                    notes=payment_notes,
                    date=datetime.utcnow().strftime("%Y-%m-%d"),
                    time=datetime.utcnow().strftime("%H:%M:%S"),
                )
                await create_transaction(engine, vendor_id, tx_payload)
                logger.info(f"💰 [INVOICING] Walk-in transaction: ₹{amount_paid} via {payment_method} for {booking_id}")
            else:
                logger.info(f"ℹ️ [INVOICING] No payment details for walk-in {booking_id} — invoice left as SENT")

        return invoice

    except Exception as e:
        logger.error(f"❌ [INVOICING] Failed for booking {booking_doc.get('_id')}: {str(e)}")
        logger.error(traceback.format_exc())
        return None





async def send_invoice_notification(
    engine: AIOEngine,
    vendor_id: str,
    invoice_id: str,
    channels: List[str] = ["email"],
    background_tasks: Optional[BackgroundTasks] = None
) -> bool:
    """
    Manually trigger invoice notification across specified channels.
    """
    invoice = await get_invoice_by_id(engine, vendor_id, invoice_id)
    
    # Fetch customer/user details
    user_engine = get_secondary_engine()
    user_col = user_engine.database.get_collection("users")
    user_info_col = user_engine.database.get_collection("userInfo")
    
    uid = ObjectId(invoice.customer_id) if ObjectId.is_valid(invoice.customer_id) else invoice.customer_id
    raw_user = await user_col.find_one({"_id": uid}) if invoice.customer_id else None
    
    user_email = ""
    user_phone = ""
    user_name = "Customer"
    
    if raw_user:
        user_email = raw_user.get("email", "")
        user_phone = raw_user.get("phoneNumber") or raw_user.get("phone", "")
        
        user_info = await user_info_col.find_one({"userId": DBRef("users", uid)})
        if not user_info:
            user_info = await user_info_col.find_one({"userId": uid})
            
        if user_info and user_info.get("name"):
            user_name = user_info.get("name")
        else:
            user_name = raw_user.get("name") or raw_user.get("username") or raw_user.get("firstName", "Customer")

    event_data = await build_invoice_event_payload(engine, invoice, user_name, user_phone, user_email, channels)
    if background_tasks:
        background_tasks.add_task(
            _publish_invoice_event_sync,
            EventType.INVOICE_SENT,
            invoice.invoice_number,
            event_data
        )
    else:
        event_publisher.publish(
            event_type=EventType.INVOICE_SENT,
            source=EventSource.VENDOR_SERVICE,
            data=event_data
        )
    
    # Update status to SENT if it was DRAFT
    if invoice.status == InvoiceStatus.DRAFT:
        invoice.status = InvoiceStatus.SENT
        await engine.save(invoice)
        
    return True


def _publish_invoice_event_sync(
    event_type: EventType,
    invoice_number: str,
    data: dict
):
    """Synchronous background task for publishing invoice events"""
    try:
        from notifications.events.publisher import event_publisher
        from notifications.events.types import EventSource
        
        event_publisher.publish(
            event_type=event_type,
            source=EventSource.VENDOR_SERVICE,
            data=data
        )
        print(f"[INVOICE] ✅ Background event published for {invoice_number}")
    except Exception as e:
        print(f"[INVOICE] ❌ Background notification failed for {invoice_number}: {str(e)}")


