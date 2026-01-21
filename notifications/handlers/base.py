"""
Base handler class for all notification channels
All channel handlers must inherit from this
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class BaseNotificationHandler(ABC):
    """
    Abstract base class for notification channel handlers
    
    Each channel (email, SMS, WhatsApp, in-app) implements this interface
    """
    
    def __init__(self):
        self.channel_name = self.__class__.__name__.replace("Handler", "").lower()
    
    @abstractmethod
    async def send(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send notification through this channel
        
        Args:
            notification_data: Dictionary containing notification details
                - notification_id: str
                - recipient_email/phone/whatsapp: str (depending on channel)
                - subject: str
                - message: str
                - data: dict (template variables)
                - template_id: str
        
        Returns:
            Dictionary with:
                - success: bool
                - message: str (success/error message)
                - metadata: dict (channel-specific response data)
        
        Raises:
            Exception: If sending fails (will be caught by worker for retry)
        """
        pass
    
    def validate_recipient(self, notification_data: Dict[str, Any]) -> bool:
        """
        Validate that notification has required recipient info for this channel
        Override in subclass if needed
        """
        return True
    
    async def prepare_content(self, notification_data: Dict[str, Any]) -> str:
        """
        Prepare notification content (can include template rendering)
        Override in subclass for custom formatting
        """
        # Default: use message if provided, otherwise use subject
        return notification_data.get("message") or notification_data.get("subject", "")
    
    def log_success(self, notification_id: str, metadata: Dict[str, Any] = None):
        """Log successful delivery"""
        logger.info(f"✅ [{self.channel_name}] Notification {notification_id} sent successfully")
        if metadata:
            logger.debug(f"   Metadata: {metadata}")
    
    def log_failure(self, notification_id: str, error: str):
        """Log failed delivery"""
        logger.error(f"❌ [{self.channel_name}] Notification {notification_id} failed: {error}")
