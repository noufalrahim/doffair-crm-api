import asyncio
from core.database import get_engine
from vendor.models.invoice import Invoice
from notifications.services.pdf_service import pdf_service
from vendor.services.invoice_service import build_invoice_event_payload

async def main():
    engine = get_engine()
    invoice = await engine.find_one(Invoice, sort=Invoice.created_at.desc())
    if not invoice:
        print("No invoice found!")
        return

    payload = await build_invoice_event_payload(
        engine, invoice, "Customer", "0000", "test@test.com"
    )
    
    # Try generating
    try:
        pdf_content = pdf_service.generate_invoice_pdf(payload)
        with open("test.pdf", 'wb') as f:
            f.write(pdf_content)
        print("SUCCESS! PDF Generated:", len(pdf_content), "bytes")
    except Exception as e:
        print("FAIL! Error:", str(e))

asyncio.run(main())
