"""
Invoice utility functions for calculations and number generation
"""
from datetime import datetime
from typing import Dict, List
from vendor.models.invoice import InvoiceTaxConfig
from core.enums import TaxType
import logging

logger = logging.getLogger(__name__)


def generate_invoice_number(vendor_id: str, current_year: int, sequence: int) -> str:
    """
    Generate unique invoice number
    Format: INV-{YEAR}-{VENDOR_SHORT}-{SEQUENCE}
    Example: INV-2026-V123-0001
    """
    vendor_short = vendor_id[:8]  # First 8 chars of vendor ID
    sequence_str = str(sequence).zfill(4)  # Pad with zeros: 0001, 0002, etc.
    return f"INV-{current_year}-{vendor_short}-{sequence_str}"


def calculate_line_item_totals(
    quantity: float,
    unit_price: float,
    discount_amount: float = 0.0,
    discount_percentage: float = 0.0,
    tax_percentage: float = 0.0
) -> Dict[str, float]:
    """
    Calculate all amounts for a single line item
    
    Returns:
        {
            'subtotal': float,
            'total_after_discount': float,
            'tax_amount': float,
            'total': float
        }
    """
    # Step 1: Calculate subtotal
    subtotal = quantity * unit_price
    
    # Step 2: Apply discounts
    discount_from_percentage = (subtotal * discount_percentage) / 100.0
    total_discount = discount_amount + discount_from_percentage
    total_after_discount = max(0, subtotal - total_discount)
    
    # Step 3: Calculate tax
    tax_amount = (total_after_discount * tax_percentage) / 100.0
    
    # Step 4: Final total
    total = total_after_discount + tax_amount
    
    return {
        'subtotal': round(subtotal, 2),
        'total_after_discount': round(total_after_discount, 2),
        'tax_amount': round(tax_amount, 2),
        'total': round(total, 2)
    }


def calculate_invoice_totals(
    line_items_total: float,
    discount_amount: float = 0.0,
    discount_percentage: float = 0.0,
    tax_config: InvoiceTaxConfig = None,
    service_charge_amount: float = 0.0,
    other_charges: Dict[str, float] = None
) -> Dict[str, float]:
    """
    Calculate invoice-level totals with tax breakdown
    
    Args:
        line_items_total: Sum of all line items
        discount_amount: Flat discount
        discount_percentage: Percentage discount
        tax_config: Tax configuration object
        service_charge_amount: Service charge amount
        other_charges: Dict of additional charges
    
    Returns:
        Complete breakdown of all amounts
    """
    other_charges = other_charges or {}
    
    # Step 1: Calculate discount
    discount_from_percentage = (line_items_total * discount_percentage) / 100.0
    total_discount = discount_amount + discount_from_percentage
    
    # Step 2: Amount after discount
    amount_after_discount = max(0, line_items_total - total_discount)
    
    # Step 3: Add service charge and other charges
    total_other_charges = sum(other_charges.values())
    total_before_tax = amount_after_discount + service_charge_amount + total_other_charges
    
    # Step 4: Calculate taxes
    tax_amount = 0.0
    cgst_amount = 0.0
    sgst_amount = 0.0
    igst_amount = 0.0
    tax_type = TaxType.NONE
    
    if tax_config and tax_config.is_active:
        tax_type = tax_config.tax_type
        
        if tax_type == TaxType.GST:
            # Simple GST (combined)
            tax_amount = (total_before_tax * tax_config.tax_percentage) / 100.0
            
        elif tax_type == TaxType.CGST_SGST:
            # Split GST (intra-state)
            cgst_amount = (total_before_tax * tax_config.cgst_percentage) / 100.0
            sgst_amount = (total_before_tax * tax_config.sgst_percentage) / 100.0
            tax_amount = cgst_amount + sgst_amount
            
        elif tax_type == TaxType.IGST:
            # Integrated GST (inter-state)
            igst_amount = (total_before_tax * tax_config.tax_percentage) / 100.0
            tax_amount = igst_amount
            
        elif tax_type in [TaxType.VAT, TaxType.CUSTOM]:
            # VAT or custom tax
            tax_amount = (total_before_tax * tax_config.tax_percentage) / 100.0
    
    # Step 5: Grand total
    grand_total = total_before_tax + tax_amount
    
    return {
        'subtotal': round(line_items_total, 2),
        'discount_amount': round(total_discount, 2),
        'total_before_tax': round(total_before_tax, 2),
        'tax_type': tax_type,
        'tax_amount': round(tax_amount, 2),
        'cgst_amount': round(cgst_amount, 2),
        'sgst_amount': round(sgst_amount, 2),
        'igst_amount': round(igst_amount, 2),
        'service_charge': round(service_charge_amount, 2),
        'other_charges': {k: round(v, 2) for k, v in other_charges.items()},
        'total_tax': round(tax_amount, 2),
        'grand_total': round(grand_total, 2)
    }


def calculate_balance_due(grand_total: float, paid_amount: float) -> float:
    """Calculate remaining balance"""
    return max(0, round(grand_total - paid_amount, 2))


def validate_invoice_edit_allowed(invoice_status: str) -> bool:
    """
    Check if invoice can be edited
    Only DRAFT invoices can be edited
    """
    from core.enums import InvoiceStatus
    return invoice_status == InvoiceStatus.DRAFT


def validate_invoice_send_allowed(invoice_status: str) -> bool:
    """
    Check if invoice can be sent
    Can send DRAFT, GENERATED, or resend SENT invoices
    """
    from core.enums import InvoiceStatus
    allowed_statuses = [InvoiceStatus.DRAFT, InvoiceStatus.GENERATED, InvoiceStatus.SENT]
    return invoice_status in [s.value for s in allowed_statuses]


def validate_invoice_cancel_allowed(invoice_status: str) -> bool:
    """
    Check if invoice can be cancelled
    Cannot cancel PAID, REFUNDED, or already CANCELLED invoices
    """
    from core.enums import InvoiceStatus
    disallowed_statuses = [InvoiceStatus.PAID, InvoiceStatus.REFUNDED, InvoiceStatus.CANCELLED]
    return invoice_status not in [s.value for s in disallowed_statuses]
