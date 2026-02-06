"""
Invoice models for post-service billing
Supports auto-generation, tax configuration, and audit trails
"""
from datetime import datetime
from odmantic import Model, Field
from typing import Optional, List, Dict, Any
from core.enums import InvoiceStatus, TaxType


class InvoiceLineItem(Model):
    """
    Individual line items within an invoice
    """
    invoice_id: str
    
    # Item details
    description: str
    quantity: float = 1.0
    unit_price: float
    
    # Discounts
    discount_amount: float = 0.0
    discount_percentage: float = 0.0
    
    # Calculated amounts
    subtotal: float  # quantity * unit_price
    total_after_discount: float  # subtotal - discount
    
    # Tax details
    tax_amount: float = 0.0
    tax_percentage: float = 0.0
    
    # Final amount
    total: float  # total_after_discount + tax
    
    # Metadata
    item_type: str = "SERVICE"  # SERVICE, PRODUCT, FEE, ADDON
    service_id: Optional[str] = None
    notes: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "collection": "invoice_line_items",
        "indexes": [
            {"fields": ["invoice_id"]},
        ],
    }


class InvoiceTaxConfig(Model):
    """
    Tax configuration per vendor/location
    Allows configurable tax rules
    """
    vendor_id: str
    location_id: Optional[str] = None  # If None, applies to all locations
    
    # Tax configuration
    tax_type: TaxType
    tax_name: str  # "GST", "CGST+SGST", "IGST", etc.
    tax_percentage: float  # 18.0 for 18% GST
    
    # For split taxes (CGST + SGST)
    cgst_percentage: float = 0.0
    sgst_percentage: float = 0.0
    
    # Additional charges
    service_charge_percentage: float = 0.0
    other_charges: Dict[str, float] = {}  # {"delivery_fee": 50.0}
    
    # Settings
    is_active: bool = True
    is_default: bool = False
    
    # Metadata
    notes: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "collection": "invoice_tax_configs",
        "indexes": [
            {"fields": ["vendor_id"]},
            {"fields": ["vendor_id", "location_id"]},
            {"fields": ["vendor_id", "is_default"]},
        ],
    }


class Invoice(Model):
    """
    Main invoice document
    Auto-generated from bookings with full audit trail
    """
    # Relationships
    vendor_id: str
    customer_id: str
    booking_id: str
    
    # Invoice identifiers
    invoice_number: str  # Auto-generated: INV-2026-0001
    invoice_date: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = Field(default=None)
    
    # Customer details (cached for invoice record)
    customer_name: str
    customer_email: str
    customer_phone: str
    customer_address: Optional[str] = None
    
    # Vendor details (cached)
    vendor_name: str
    vendor_email: str
    vendor_phone: str
    vendor_address: Optional[str] = None
    vendor_gstin: Optional[str] = None  # GST Identification Number
    
    # Booking details
    service_name: str
    service_date: datetime
    
    # Financial details
    subtotal: float  # Sum of all line items before tax/discount
    discount_amount: float = 0.0
    discount_percentage: float = 0.0
    
    # Tax breakdown
    tax_type: TaxType = TaxType.NONE
    tax_amount: float = 0.0
    cgst_amount: float = 0.0
    sgst_amount: float = 0.0
    igst_amount: float = 0.0
    
    # Additional charges
    service_charge: float = 0.0
    other_charges: Dict[str, float] = {}
    
    # Totals
    total_before_tax: float  # subtotal - discount + other_charges
    total_tax: float  # sum of all taxes
    grand_total: float  # final amount to pay
    
    # Payment tracking
    paid_amount: float = 0.0
    balance_due: float  # grand_total - paid_amount
    
    # Status
    status: InvoiceStatus = InvoiceStatus.DRAFT
    
    # Notifications
    sent_at: Optional[datetime] = Field(default=None)
    sent_count: int = 0  # Number of times invoice was sent
    
    # Cancellation
    cancelled_at: Optional[datetime] = Field(default=None)
    cancellation_reason: Optional[str] = None
    cancelled_by: Optional[str] = None  # vendor_id who cancelled
    
    # Payment
    payment_received_at: Optional[datetime] = Field(default=None)
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    
    # Additional info
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    
    # Metadata
    is_active: bool = True
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "collection": "invoices",
        "indexes": [
            {"fields": ["vendor_id"]},
            {"fields": ["customer_id"]},
            {"fields": ["booking_id"]},
            {"fields": ["invoice_number"], "unique": True},
            {"fields": ["status"]},
            {"fields": ["invoice_date"]},
            {"fields": ["due_date"]},
            {"fields": ["vendor_id", "status"]},
            {"fields": ["customer_id", "status"]},
        ],
    }


class InvoiceAuditLog(Model):
    """
    Complete audit trail for all invoice operations
    Immutable record of all changes
    """
    invoice_id: str
    invoice_number: str
    
    # Action details
    action: str  # From InvoiceAuditAction enum
    performed_by: str  # vendor_id
    performed_by_role: str = "vendor"  # vendor, system, admin
    
    # Changes (for EDITED action)
    field_changed: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    
    # Context
    reason: Optional[str] = None
    notes: Optional[str] = None
    
    # Metadata
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "collection": "invoice_audit_logs",
        "indexes": [
            {"fields": ["invoice_id"]},
            {"fields": ["invoice_id", "timestamp"]},
            {"fields": ["performed_by"]},
            {"fields": ["action"]},
        ],
    }
