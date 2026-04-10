from dotenv import load_dotenv
load_dotenv()
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:     %(name)s - %(message)s"
)
# Ensure app loggers show INFO level
for _logger_name in ["vendor.routers.bookings", "notifications.events.publisher", "notifications.events.consumer", "notifications.handlers.email_handler", "notifications.handlers.sms_handler"]:
    logging.getLogger(_logger_name).setLevel(logging.INFO)
from fastapi import FastAPI
import asyncio
from contextlib import asynccontextmanager
from core.socket_manager import socket_app, sio, redis_listener
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
from vendor.routers import medications as vendor_medications_router
from vendor.routers import sessions as vendor_sessions_router
from vendor.routers import prescriptions_data as vendor_prescriptions_data_router
from vendor.routers import transactions as vendor_transactions_router
from vendor.routers import store_items as vendor_store_items_router
from vendor.routers import documents as vendor_documents_router
from vendor.routers import notifications as vendor_notifications_router
from internal.routers import reviews as internal_reviews_router


from core.config import settings
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.proxy_headers import ProxyHeadersMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start Redis listener for WebSockets in the background
    listener_task = asyncio.create_task(redis_listener())
    yield
    # Clean up
    listener_task.cancel()
    try:
        await listener_task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="Doffair API", 
    swagger_ui_parameters={"persistAuthorization": True},
    lifespan=lifespan
)

# Mount Socket.IO
app.mount("/socket.io", socket_app)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

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

# Vendor structured prescription system
app.include_router(vendor_medications_router.router)
app.include_router(vendor_sessions_router.router)
app.include_router(vendor_prescriptions_data_router.router)
app.include_router(vendor_transactions_router.router)
app.include_router(vendor_store_items_router.router)
app.include_router(vendor_documents_router.router)
app.include_router(vendor_notifications_router.router)

# Notification routers
app.include_router(notifications_router.router)
app.include_router(events_router.router)

# Internal routers
app.include_router(internal_reviews_router.router)
