import os
from notifications.templates.renderer import template_renderer
from notifications.events.types import EventType, RecipientRole
from notifications.enums import NotificationChannel
from jinja2 import Environment, FileSystemLoader

# Mock context for invoice
context = {
    "invoice_number": "INV-2026-TEST",
    "invoice_date": "2026-04-11",
    "invoice_time": "12:00 PM",
    "legal_name": "Doffair Test Vendor Ltd",
    "store_name": "Test Store Location",
    "store_address": "123 Pet Street, Dog City, 560001",
    "vendor_phone": "9876543210",
    "vendor_gstin": "29AAAAA0000A1Z5",
    "vendor_state": "Karnataka",
    "customer_name": "Jane User",
    "user_phone": "9999999999",
    "customer_pincode": "560002",
    "items": [
        {"name": "Pet Grooming Service", "hsn_sac": "9985", "mrp": 1000.0, "quantity": 1, "unit_price": 1000.0, "discount_amount": 0.0, "taxable_value": 847.46, "tax_rate": 18.0, "tax_amount": 152.54, "subtotal": 1000.0}
    ],
    "grand_total": "1,000.00",
    "grand_total_words": "One Thousand Rupees Only",
    "balance_due": "0.00",
    "tax_details": {"SGST": 76.27, "CGST": 76.27},
    "rounding_off": "0.00",
    "raw_grand_total": "1000.00"
}

def mock_pdf_render():
    # We'll render to HTML first to see if SVG is there
    # The renderer handles the injection of doffair_logo_svg
    html = template_renderer.render(
        event_type=EventType.INVOICE_SENT,
        recipient_role=RecipientRole.USER,
        channel=NotificationChannel.EMAIL,  # We use this to get the context first
        context=context
    )
    
    # Actually, we want the PDF template
    # TemplateRenderer has a way to get templates
    template_path = "notifications/templates/INVOICE_SENT/user/invoice_pdf.html"
    env = Environment(loader=FileSystemLoader("."))
    
    # Renderer context
    from notifications.config.logo import DOFFAIR_LOGO_SVG, BRANDING_COLOR
    full_context = {
        "doffair_logo_svg": DOFFAIR_LOGO_SVG,
        "branding_color": BRANDING_COLOR,
        **context
    }
    
    template = env.get_template(template_path)
    rendered_html = template.render(full_context)
    
    with open("test_invoice_pdf_view.html", "w") as f:
        f.write(rendered_html)
    print("Rendered PDF template to test_invoice_pdf_view.html for visual check")

if __name__ == "__main__":
    mock_pdf_render()
