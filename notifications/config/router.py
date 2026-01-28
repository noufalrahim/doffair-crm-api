import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from notifications.events.types import EventType, RecipientRole
from notifications.enums import NotificationChannel

logger = logging.getLogger(__name__)


class NotificationRouter:
    def __init__(self):
        self._routing_config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        try:
            config_path = Path(__file__).parent / "routing.json"
            
            if not config_path.exists():
                logger.error(f"❌ Routing config not found: {config_path}")
                raise FileNotFoundError(f"Routing config not found: {config_path}")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                self._routing_config = json.load(f)
            
            logger.info(f"✅ Loaded routing config for {len(self._routing_config)} event types")
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in routing config: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to load routing config: {str(e)}")
            raise
    
    def get_recipients(self, event_type: EventType) -> List[RecipientRole]:
        try:
            # Handle both EventType enum and string values
            event_type_str = event_type.value if hasattr(event_type, 'value') else str(event_type)
            event_config = self._routing_config.get(event_type_str, {})
            
            if not event_config:
                logger.warning(f"⚠️ No routing config for event type: {event_type_str}")
                return []
            
            recipients = event_config.get("recipients", [])
            
            return [RecipientRole(r) for r in recipients]
            
        except Exception as e:
            event_type_str = event_type.value if hasattr(event_type, 'value') else str(event_type)
            logger.error(f"❌ Failed to get recipients for {event_type_str}: {str(e)}")
            return []
    
    def get_channels(self, event_type: EventType, recipient_role: RecipientRole) -> List[NotificationChannel]:
        try:
            # Handle both EventType enum and string values
            event_type_str = event_type.value if hasattr(event_type, 'value') else str(event_type)
            recipient_role_str = recipient_role.value if hasattr(recipient_role, 'value') else str(recipient_role)
            
            event_config = self._routing_config.get(event_type_str, {})
            
            if not event_config:
                logger.warning(f"⚠️ No routing config for event type: {event_type_str}")
                return []
            
            channels_config = event_config.get("channels", {})
            channels = channels_config.get(recipient_role_str, [])
            
            return [NotificationChannel(c) for c in channels]
            
        except Exception as e:
            event_type_str = event_type.value if hasattr(event_type, 'value') else str(event_type)
            recipient_role_str = recipient_role.value if hasattr(recipient_role, 'value') else str(recipient_role)
            logger.error(
                f"❌ Failed to get channels for {event_type_str}, "
                f"role {recipient_role_str}: {str(e)}"
            )
            return []
    
    def get_priority(self, event_type: EventType) -> str:
        try:
            # Handle both EventType enum and string values
            event_type_str = event_type.value if hasattr(event_type, 'value') else str(event_type)
            event_config = self._routing_config.get(event_type_str, {})
            return event_config.get("priority", "medium")
        except Exception as e:
            event_type_str = event_type.value if hasattr(event_type, 'value') else str(event_type)
            logger.error(f"❌ Failed to get priority for {event_type_str}: {str(e)}")
            return "medium"
    
    def reload_config(self):
        logger.info("🔄 Reloading routing configuration...")
        self._load_config()


notification_router = NotificationRouter()
