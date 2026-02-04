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




class VendorStatus(str, Enum):
    PHONE_VERIFIED = "PHONE_VERIFIED"
    BASIC_INFO_SUBMITTED = "BASIC_INFO_SUBMITTED"
    SERVICE_TYPE_SELECTED = "SERVICE_TYPE_SELECTED"
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
    CENTER = "CENTER"   # only at vendor location
    HOME = "HOME"       # only at customer location
    BOTH = "BOTH"       # vendor + home

class BookingStatus(str, Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"      # User created booking, payment not done
    PAYMENT_FAILED = "PAYMENT_FAILED"        # Payment failed
    PENDING_APPROVAL = "PENDING_APPROVAL"    # Payment done, waiting for vendor
    CONFIRMED = "CONFIRMED"                  # Vendor approved
    REJECTED = "REJECTED"                    # Vendor rejected
    COMPLETED = "COMPLETED"                  # Service completed
    CANCELLED = "CANCELLED"                  # User/Vendor cancelled
    OFFLINE = "OFFLINE"                      # Offline booking

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