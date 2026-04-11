import asyncio
from core.database import get_engine
from vendor.models.invoice import Invoice
from vendor.services.invoice_service import send_invoice_notification

async def main():
    engine = get_engine()
    invoice = await engine.find_one(Invoice, sort=Invoice.created_at.desc())
    if not invoice:
        print("No invoice found!")
        return

    print(f"Triggering email for invoice {invoice.invoice_number}")
    
    await send_invoice_notification(
        engine,
        vendor_id=invoice.vendor_id,
        invoice_id=str(invoice.id)
    )
    print("Done")

asyncio.run(main())
