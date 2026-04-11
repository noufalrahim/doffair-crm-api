import re

with open("vendor/services/invoice_service.py", "r") as f:
    content = f.read()

helper = """
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
"""

if "async def build_invoice_event_payload" not in content:
    idx = content.find("async def handle_booking_completion_invoicing")
    content = content[:idx] + helper + "\n\n" + content[idx:]

# Define replacements
repl1_search = r'        event_data = \{\n(?:.|\n)*?            "template_id": "InvoiceSent"\n        \}'
repl1_replace = r'        event_data = await build_invoice_event_payload(engine, invoice, resolved_name, resolved_phone, resolved_email)'

repl2_search = r'        event_data = \{\n(?:.|\n)*?                "template_id": "InvoiceSent"\n        \}'
repl2_replace = r'        event_data = await build_invoice_event_payload(engine, invoice, user.name if user else "Customer", user.phone if user else "", user.email if user else "")'

repl3_search_start = r'    # Fetch vendor'
repl3_search_end = r'        "template_id": "InvoiceSent"\n    \}'
# Find the exact text index for replaced block 3
start_idx = content.find("    # Fetch vendor\n    vendor = await engine.find_one")
end_idx = content.find('"template_id": "InvoiceSent"\n    }', start_idx)
if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + '    event_data = await build_invoice_event_payload(engine, invoice, user_name, user_phone, user_email, channels)' + content[end_idx + 35:]

content = re.sub(repl1_search, repl1_replace, content, count=1)
content = re.sub(repl2_search, repl2_replace, content, count=1)

with open("vendor/services/invoice_service.py", "w") as f:
    f.write(content)
print("done patching")
