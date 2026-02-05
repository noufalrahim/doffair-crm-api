"""
Invoice schemas for API requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from core.enums import InvoiceStatus, TaxType


# ============================================
# Line Item Schemas
# ============================================

class InvoiceLineItemCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    quantity: float = Field(1.0, gt=0)
    unit_price: float = Field(..., gt=0)
    discount_amount: float = Field(0.0, ge=0)
    discount_percentage: float = Field(0.0, ge=0, le=100)
    tax_percentage: float = Field(0.0, ge=0, le=100)
    item_type: str = Field("SERVICE", description="SERVICE, PRODUCT, FEE, ADDON")
    service_id: Optional[str] = None
    notes: Optional[str] = None


class InvoiceLineItemResponse(BaseModel):
    id: str
    description: str
    quantity: float
    unit_price: float
    discount_amount: float
    discount_percentage: float
    subtotal: float
    total_after_discount: float
    tax_amount: float
    tax_percentage: float
    total: float
    item_type: str
    service_id: Optional[str]
    notes: Optional[str]


# ============================================
# Tax Configuration Schemas
# ============================================

class TaxConfigCreate(BaseModel):
    location_id: Optional[str] = Field(None, description="Leave None for vendor-wide config")
    tax_type: TaxType
    tax_name: str = Field(..., min_length=1, max_length=100, description="Display name like 'GST 18%'")
    tax_percentage: float = Field(..., ge=0, le=100)
    cgst_percentage: float = Field(0.0, ge=0, le=100)
    sgst_percentage: float = Field(0.0, ge=0, le=100)
    service_charge_percentage: float = Field(0.0, ge=0, le=100)
    other_charges: Dict[str, float] = Field(default_factory=dict)
    is_default: bool = False
    notes: Optional[str] = None


class TaxConfigUpdate(BaseModel):
    tax_name: Optional[str] = None
    tax_percentage: Optional[float] = Field(None, ge=0, le=100)
    cgst_percentage: Optional[float] = Field(None, ge=0, le=100)
    sgst_percentage: Optional[float] = Field(None, ge=0, le=100)
    service_charge_percentage: Optional[float] = Field(None, ge=0, le=100)
    other_charges: Optional[Dict[str, float]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    notes: Optional[str] = None


class TaxConfigResponse(BaseModel):
    id: str
    vendor_id: str
    location_id: Optional[str]
    tax_type: TaxType
    tax_name: str
    tax_percentage: float
    cgst_percentage: float
    sgst_percentage: float
    service_charge_percentage: float
    other_charges: Dict[str, float]
    is_active: bool
    is_default: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


# ============================================
# Invoice Schemas
# ============================================

class InvoiceGenerateRequest(BaseModel):
    """Generate invoice from completed booking"""
    booking_id: str
    due_days: int = Field(30, ge=0, le=365, description="Days until payment due")
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    auto_send: bool = Field(True, description="Automatically send to customer")


class InvoiceCreateManualRequest(BaseModel):
    """Manually create invoice (not from booking)"""
    customer_id: str
    customer_name: str
    customer_email: str
    customer_phone: str
    customer_address: Optional[str] = None
    
    service_name: str
    service_date: datetime
    
    line_items: List[InvoiceLineItemCreate]
    
    discount_amount: float = Field(0.0, ge=0)
    discount_percentage: float = Field(0.0, ge=0, le=100)
    
    tax_config_id: Optional[str] = Field(None, description="Use specific tax config")
    
    due_days: int = Field(30, ge=0, le=365)
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    auto_send: bool = True


class InvoiceUpdateRequest(BaseModel):
    """Update invoice details (only for DRAFT status)"""
    line_items: Optional[List[InvoiceLineItemCreate]] = None
    discount_amount: Optional[float] = Field(None, ge=0)
    discount_percentage: Optional[float] = Field(None, ge=0, le=100)
    due_date: Optional[datetime] = None
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None


class InvoiceMarkPaidRequest(BaseModel):
    """Mark invoice as paid"""
    paid_amount: float = Field(..., gt=0)
    payment_method: str = Field(..., description="CASH, UPI, CARD, BANK_TRANSFER, etc.")
    payment_reference: Optional[str] = Field(None, description="Transaction ID or reference")
    payment_date: Optional[datetime] = None
    notes: Optional[str] = None


class InvoiceCancelRequest(BaseModel):
    """Cancel invoice"""
    reason: str = Field(..., min_length=10, max_length=500)


class InvoiceResendRequest(BaseModel):
    """Resend invoice to customer"""
    channels: List[str] = Field(["email"], description="Channels: email, sms, whatsapp")
    notes: Optional[str] = None


class InvoiceResponse(BaseModel):
    """Complete invoice response"""
    id: str
    vendor_id: str
    customer_id: str
    booking_id: str
    
    invoice_number: str
    invoice_date: datetime
    due_date: Optional[datetime]
    
    customer_name: str
    customer_email: str
    customer_phone: str
    customer_address: Optional[str]
    
    vendor_name: str
    vendor_email: str
    vendor_phone: str
    vendor_address: Optional[str]
    vendor_gstin: Optional[str]
    
    service_name: str
    service_date: datetime
    
    subtotal: float
    discount_amount: float
    discount_percentage: float
    
    tax_type: TaxType
    tax_amount: float
    cgst_amount: float
    sgst_amount: float
    igst_amount: float
    
    service_charge: float
    other_charges: Dict[str, float]
    
    total_before_tax: float
    total_tax: float
    grand_total: float
    
    paid_amount: float
    balance_due: float
    
    status: InvoiceStatus
    
    sent_at: Optional[datetime]
    sent_count: int
    
    cancelled_at: Optional[datetime]
    cancellation_reason: Optional[str]
    
    payment_received_at: Optional[datetime]
    payment_method: Optional[str]
    payment_reference: Optional[str]
    
    notes: Optional[str]
    terms_and_conditions: Optional[str]
    
    created_at: datetime
    updated_at: datetime


class InvoiceListResponse(BaseModel):
    """Simplified invoice for list views"""
    id: str
    invoice_number: str
    invoice_date: datetime
    due_date: Optional[datetime]
    customer_name: str
    service_name: str
    grand_total: float
    paid_amount: float
    balance_due: float
    status: InvoiceStatus
    sent_count: int
    created_at: datetime


class InvoiceAuditLogResponse(BaseModel):
    """Audit log entry"""
    id: str
    invoice_number: str
    action: str
    performed_by: str
    performed_by_role: str
    field_changed: Optional[str]
    old_value: Optional[str]
    new_value: Optional[str]
    reason: Optional[str]
    notes: Optional[str]
    timestamp: datetime
