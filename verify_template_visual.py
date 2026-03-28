import sys
from pathlib import Path
from datetime import datetime
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jinja2 import Environment, FileSystemLoader

def verify_template():
    # Setup Jinja2 environment
    template_dir = Path(__file__).parent / "notifications/templates/INVOICE_SENT/user"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    
    try:
        template = env.get_template("invoice_pdf.html")
    except Exception as e:
        print(f"Error loading template: {e}")
        return

    # Mock Data matching the sample image
    mock_data = {
        "invoice_number": "25-INV-WF-2448",
        "invoice_date": datetime(2026, 3, 26, 18, 4),
        "vendor_name": "EVERTUSK DISTRIBUTIONS PRIVATE LIMITED",
        "vendor_address": "Roms N Raks Pet Store No 441/343, Ground Floor Opposite D Mart Whitefield, Main Road Siddapura, Bangalore Karnataka 560066",
        "vendor_gstin": "29AAICE2439G1Z",
        "vendor_phone": "8589010081",
        "customer_name": "Mourya",
        "customer_phone": "9985750207",
        "customer_pincode": "560066",
        "status": "paid",
        "grand_total": 1351.0,
        "rounding_off": 0.35,
        "tax_details": {
            "sgst 9.0%": 35.01,
            "cgst 9.0%": 35.01,
            "sgst 2.5%": 21.23,
            "cgst 2.5%": 21.23
        },
        "items": [
            {
                "name": "Bb Fofos Flexy Ball Ultra Bounce Toy-M",
                "hsn_sac": "39269069",
                "mrp": 540.0,
                "quantity": 1,
                "unit_price": 540.0,
                "discount_amount": 81.0,
                "taxable_value": 388.98,
                "tax_rate": 18.0,
                "tax_amount": 70.02,
                "subtotal": 459.0
            },
            {
                "name": "Pets Way Dog T-shirt Printed 5XL",
                "hsn_sac": "61099010",
                "mrp": 1049.0,
                "quantity": 1,
                "unit_price": 1049.0,
                "discount_amount": 157.35,
                "taxable_value": 849.19,
                "tax_rate": 5.0,
                "tax_amount": 42.46,
                "subtotal": 891.65
            }
        ]
    }

    rendered_html = template.render(**mock_data)
    
    output_path = Path("/Users/noufalrahim/Desktop/Projects/DoffairMarketplace/doffair-python-vendor/tmp/test_invoice.html")
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, "w") as f:
        f.write(rendered_html)
    
    print(f"Template rendered successfully to {output_path}")
    return str(output_path)

if __name__ == "__main__":
    verify_template()
