from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings

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


# ✅ CREATE APP ONCE
app = FastAPI(title=settings.APP_NAME)

# ✅ ADD CORS ON SAME APP
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ INCLUDE ROUTERS
app.include_router(admin_auth_router.router)
app.include_router(service_type_router.router)
app.include_router(vendor_onboarding_router.router)
app.include_router(vendor_auth_router.router)
app.include_router(vendor_service_type_router.router)
app.include_router(vendor_locations_router.router)
app.include_router(vendor_services_router.router)
app.include_router(vendor_images_router.router)
app.include_router(admin_vendors_router.router)
app.include_router(admin_amenities_router.router)
app.include_router(vendor_amenities_router.router)
app.include_router(vendor_service_area_router.router)
app.include_router(doctors.router)
app.include_router(doctor_availability.router)
app.include_router(pricing.router)
