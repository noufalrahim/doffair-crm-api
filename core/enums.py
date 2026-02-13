from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    VENDOR = "vendor"
    USER = "user"

class VendorRole(str, Enum):
    ADMIN = "vendor_admin"
    MANAGER = "vendor_manager"
    STAFF = "vendor_staff"

class ServiceMode(str, Enum):
    BOOKING = "booking"
    LEAD = "lead"

class DogSize(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"




class VendorStatus(str, Enum):
    PHONE_VERIFIED = "PHONE_VERIFIED"
    BASIC_INFO_SUBMITTED = "BASIC_INFO_SUBMITTED"
    VERTICAL_SELECTED = "VERTICAL_SELECTED"
    LOCATION_ADDED = "LOCATION_ADDED"
    SERVICES_CONFIGURED = "SERVICES_CONFIGURED"
    PRICING_CONFIGURED = "PRICING_CONFIGURED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class DiscountType(str, Enum):
    NONE = "NONE"
    FLAT = "FLAT"        # ₹200 off
    PERCENT = "PERCENT"  # 10% off

class ServiceDeliveryMode(str, Enum):
    CENTER = "In-Center"   
    HOME = "At Home"      
    BOTH = "Both"  

class BookingStatus(str, Enum):
    PENDING_PAYMENT = "pending_payment"      # User created booking, payment not done
    PAYMENT_FAILED = "payment_failed"        # Payment failed
    PENDING_APPROVAL = "pending_approval"    # Payment done, waiting for vendor
    CONFIRMED = "confirmed"                  # Vendor approved
    REJECTED = "rejected"                    # Vendor rejected
    COMPLETED = "completed"                  # Service completed
    CANCELLED = "cancelled"                  # User/Vendor cancelled
    ONGOING = "ongoing"                      # Service is in progress
    OFFLINE = "offline"                      # Offline booking

class PaymentStatus(str, Enum):
    PENDING = "PENDING"        # Payment initiated
    SUCCESS = "SUCCESS"        # Payment successful
    FAILED = "FAILED"          # Payment failed
    REFUNDED = "REFUNDED"      # Payment refunded (vendor rejected)

class ReminderType(str, Enum):
    FOLLOW_UP = "FOLLOW_UP"           # General follow-up
    MEDICATION = "MEDICATION"         # Medication reminder
    REPEAT_SERVICE = "REPEAT_SERVICE" # Service due again
    CHECKUP = "CHECKUP"              # Scheduled checkup
    CUSTOM = "CUSTOM"                # Custom reminder

class ReminderStatus(str, Enum):
    PENDING = "PENDING"    # Scheduled, not sent yet
    SENT = "SENT"          # Successfully sent
    FAILED = "FAILED"      # Failed to send
    CANCELLED = "CANCELLED" # Cancelled by vendor

class InvoiceStatus(str, Enum):
    DRAFT = "DRAFT"              # Invoice created but not finalized
    GENERATED = "GENERATED"      # Auto-generated from booking
    SENT = "SENT"                # Sent to customer
    PAID = "PAID"                # Payment received
    PARTIALLY_PAID = "PARTIALLY_PAID"  # Partial payment
    OVERDUE = "OVERDUE"          # Payment overdue
    CANCELLED = "CANCELLED"      # Invoice cancelled
    REFUNDED = "REFUNDED"        # Full refund issued

class TaxType(str, Enum):
    NONE = "NONE"                # No tax
    GST = "GST"                  # Goods and Services Tax (combined)
    CGST_SGST = "CGST_SGST"      # Central + State GST (intra-state)
    IGST = "IGST"                # Integrated GST (inter-state)
    VAT = "VAT"                  # Value Added Tax
    CUSTOM = "CUSTOM"            # Custom tax configuration

class InvoiceAuditAction(str, Enum):
    CREATED = "CREATED"          # Invoice created
    GENERATED = "GENERATED"      # Auto-generated from booking
    EDITED = "EDITED"            # Invoice edited
    SENT = "SENT"                # Invoice sent to customer
    RESENT = "RESENT"            # Invoice resent
    CANCELLED = "CANCELLED"      # Invoice cancelled
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"  # Payment marked as received
    REFUNDED = "REFUNDED"        # Invoice refunded