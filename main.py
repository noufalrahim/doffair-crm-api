from fastapi import FastAPI

from admin.routers import auth as admin_auth_router
from admin.routers import service_types as service_type_router
from vendor.routers import onboarding as vendor_onboarding_router
from vendor.routers import auth as vendor_auth_router
from vendor.routers import service_types as vendor_service_type_router
from vendor.routers import locations as vendor_locations_router
from vendor.routers import services as vendor_services_router
from vendor.routers import images as vendor_images_router
from admin.routers import vendors as admin_vendors_router
from admin.routers import amenities as admin_amenities_router
from vendor.routers import amenities as vendor_amenities_router
from vendor.routers import service_area as vendor_service_area_router
from vendor.routers import doctors, doctor_availability
from vendor.routers import pricing
from user.routers import auth as user_auth_router
from user.routers import leads as leads_router
from user.routers import pet_images as pet_images_router
from user.routers import bookings as bookings_router
from notifications.routers import notifications as notifications_router
from notifications.routers import events as events_router
from vendor.routers import offline_bookings_v2 as vendor_offline_bookings_router
from vendor.routers import helpers as vendor_helpers_router
from vendor.routers import prescriptions_v2 as vendor_prescriptions_router
from vendor.routers import reminders_v2 as vendor_reminders_router
from vendor.routers import profile as vendor_profile_router
from vendor.routers import invoices as vendor_invoices_router
from vendor.routers import bookings as vendor_bookings_router


from core.config import settings
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Doffair API", swagger_ui_parameters={"persistAuthorization": True})
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Admin routers
app.include_router(admin_auth_router.router)
app.include_router(service_type_router.router)
app.include_router(admin_vendors_router.router)
app.include_router(admin_amenities_router.router)

# Vendor routers
app.include_router(vendor_onboarding_router.router)
app.include_router(vendor_auth_router.router)
app.include_router(vendor_profile_router.router)
app.include_router(vendor_service_type_router.router)
app.include_router(vendor_locations_router.router)
app.include_router(vendor_services_router.router)
app.include_router(vendor_images_router.router)
app.include_router(vendor_amenities_router.router)
app.include_router(vendor_service_area_router.router)
app.include_router(vendor_bookings_router.router)
app.include_router(doctors.router)
app.include_router(doctor_availability.router)
app.include_router(pricing.router)

# Vendor offline booking system (WORKING)
app.include_router(vendor_offline_bookings_router.router)
app.include_router(vendor_helpers_router.router)

# Vendor prescription management
app.include_router(vendor_prescriptions_router.router)

# Vendor reminder system
app.include_router(vendor_reminders_router.router)

# Vendor invoice system
app.include_router(vendor_invoices_router.router)

# User routers
app.include_router(user_auth_router.router)
app.include_router(leads_router.router)
app.include_router(pet_images_router.router)
app.include_router(bookings_router.router)

# Notification routers
app.include_router(notifications_router.router)
app.include_router(events_router.router)
