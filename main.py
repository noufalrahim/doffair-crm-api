from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from admin.routers import auth as admin_auth_router
from admin.routers import verticals as admin_verticals_router
from vendor.routers import onboarding as vendor_onboarding_router
from vendor.routers import auth as vendor_auth_router
from vendor.routers import verticals as vendor_vertical_router
from vendor.routers import locations as vendor_locations_router
from vendor.routers import services as vendor_services_router
from admin.routers import vendors as admin_vendors_router
from admin.routers import amenities as admin_amenities_router
from admin.routers import admins as admin_admins_router
from vendor.routers import amenities as vendor_amenities_router
from vendor.routers import analytics as vendor_analytics_router
from vendor.routers import service_area as vendor_service_area_router
from vendor.routers import doctors, doctor_availability
from vendor.routers import pricing
from user.routers import auth as user_auth_router
from user.routers import leads as leads_router
from user.routers import bookings as bookings_router
from user.routers import users as users_router
from notifications.routers import notifications as notifications_router
from notifications.routers import events as events_router
from vendor.routers import offline_bookings_v2 as vendor_offline_bookings_router
from vendor.routers import helpers as vendor_helpers_router
from vendor.routers import prescriptions_v2 as vendor_prescriptions_router
from vendor.routers import reminders_v2 as vendor_reminders_router
from vendor.routers import profile as vendor_profile_router
from vendor.routers import invoices as vendor_invoices_router
from vendor.routers import bookings as vendor_bookings_router
from vendor.routers import customers as vendor_customers_router
from vendor.routers import walkins as vendor_walkins_router
from vendor.routers import care_professionals as vendor_care_professionals_router
from vendor.routers import care_professional_availability as vendor_cp_availability_router
from vendor.routers import work_info as vendor_work_info_router
from vendor.routers import media as vendor_media_router
from vendor.routers import reviews as vendor_reviews_router
from vendor.routers import bank_info as vendor_bank_info_router


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
app.include_router(admin_verticals_router.router)
app.include_router(admin_vendors_router.router)
app.include_router(admin_amenities_router.router)
app.include_router(admin_admins_router.router)

# Vendor routers
app.include_router(vendor_onboarding_router.router)
app.include_router(vendor_auth_router.router)
app.include_router(vendor_profile_router.router)
app.include_router(vendor_vertical_router.router)
app.include_router(vendor_vertical_router.router_general)
app.include_router(vendor_locations_router.router)
app.include_router(vendor_services_router.router)
app.include_router(vendor_amenities_router.router)
app.include_router(vendor_analytics_router.router)
app.include_router(vendor_service_area_router.router)
app.include_router(vendor_bookings_router.router)
app.include_router(vendor_customers_router.router)
app.include_router(vendor_walkins_router.router)
app.include_router(doctors.router)
app.include_router(doctor_availability.router)
app.include_router(pricing.router)
app.include_router(vendor_cp_availability_router.router)
app.include_router(vendor_care_professionals_router.router)
app.include_router(vendor_work_info_router.router)
app.include_router(vendor_media_router.router)
app.include_router(vendor_reviews_router.router)
app.include_router(vendor_bank_info_router.router)

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
app.include_router(bookings_router.router)
app.include_router(users_router.router)

# Notification routers
app.include_router(notifications_router.router)
app.include_router(events_router.router)
