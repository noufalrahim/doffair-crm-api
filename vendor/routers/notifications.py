from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
import logging

from core.security import get_current_vendor
from core.database import get_engine
from vendor.models.vendor_notification_settings import VendorNotificationSettings, NotificationTriggerSetting
from vendor.schemas.notification_settings import VendorNotificationSettingsUpdate, VendorNotificationSettingsResponse
from utils.response import success_response, error_response

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/vendor/settings/notifications",
    tags=["Vendor Notification Settings"]
)

@router.get("", response_model=dict)
async def get_notification_settings(
    current_vendor: dict = Depends(get_current_vendor),
    engine = Depends(get_engine)
):
    try:
        vendor_id = current_vendor["vendor_id"]
        settings = await engine.find_one(VendorNotificationSettings, VendorNotificationSettings.vendor_id == vendor_id)
        
        if not settings:
            settings = VendorNotificationSettings(vendor_id=vendor_id)
            await engine.save(settings)
            
        settings_dict = settings.model_dump()
        settings_dict['id'] = str(settings.id)
            
        return success_response(data=settings_dict).model_dump()
        
    except Exception as e:
        logger.error(f"Failed to get notification settings: {str(e)}")
        return error_response(message=f"Failed to get notification settings: {str(e)}").model_dump()


@router.put("", response_model=dict)
async def update_notification_settings(
    payload: VendorNotificationSettingsUpdate,
    current_vendor: dict = Depends(get_current_vendor),
    engine = Depends(get_engine)
):
    try:
        vendor_id = current_vendor["vendor_id"]
        settings = await engine.find_one(VendorNotificationSettings, VendorNotificationSettings.vendor_id == vendor_id)
        
        if not settings:
            settings = VendorNotificationSettings(vendor_id=vendor_id)
            
        update_data = payload.model_dump(exclude_unset=True)
        
        for field, trigger_data in update_data.items():
            if hasattr(settings, field) and trigger_data is not None:
                current_trigger = getattr(settings, field)
                for tf, tv in trigger_data.items():
                    if hasattr(current_trigger, tf):
                        setattr(current_trigger, tf, tv)
                setattr(settings, field, current_trigger)
                
        await engine.save(settings)
        
        settings_dict = settings.model_dump()
        settings_dict['id'] = str(settings.id)
            
        return success_response(data=settings_dict, message="Settings updated successfully").model_dump()
        
    except Exception as e:
        logger.error(f"Failed to update notification settings: {str(e)}")
        return error_response(message=f"Failed to update notification settings: {str(e)}").model_dump()


@router.post("/test", response_model=dict)
async def test_notification_trigger(
    trigger_name: str,
    current_vendor: dict = Depends(get_current_vendor),
    engine = Depends(get_engine)
):
    """ Simulated manual trigger test endpoint """
    try:
        vendor_id = current_vendor["vendor_id"]
        settings = await engine.find_one(VendorNotificationSettings, VendorNotificationSettings.vendor_id == vendor_id)
        
        if not settings or not hasattr(settings, trigger_name):
            return error_response(message=f"Trigger {trigger_name} not found or no settings exist").model_dump()
            
        trigger_setting = getattr(settings, trigger_name)
        
        # Test logic goes here.
        return success_response(
            message=f"Successfully tested {trigger_name}. Email={trigger_setting.send_email}, SMS={trigger_setting.send_sms}"
        ).model_dump()
        
    except Exception as e:
        logger.error(f"Failed to test notification trigger: {str(e)}")
        return error_response(message=f"Failed to test notification trigger: {str(e)}").model_dump()
