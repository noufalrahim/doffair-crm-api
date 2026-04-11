import logging
from typing import Dict, Any, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound
from notifications.events.types import EventType, RecipientRole
from notifications.enums import NotificationChannel
from notifications.config.logo import DOFFAIR_LOGO_BASE64, BRANDING_COLOR, DOFFAIR_LOGO_SVG

logger = logging.getLogger(__name__)


class TemplateRenderer:
    def __init__(self):
        self._templates_dir = Path(__file__).parent
        self._env = Environment(
            loader=FileSystemLoader(str(self._templates_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        logger.info(f"✅ Template renderer initialized with directory: {self._templates_dir}")
    
    def render(
        self,
        event_type: EventType,
        recipient_role: RecipientRole,
        channel: NotificationChannel,
        context: Dict[str, Any]
    ) -> Optional[str]:
        try:
            template_path = self._get_template_path(event_type, recipient_role, channel)
            
            if not template_path:
                # Handle both enum and string
                et_str = event_type.value if hasattr(event_type, 'value') else str(event_type)
                rr_str = recipient_role.value if hasattr(recipient_role, 'value') else str(recipient_role)
                ch_str = channel.value if hasattr(channel, 'value') else str(channel)
                logger.warning(
                    f"⚠️ Template not found for {et_str}/{rr_str}/{ch_str}"
                )
                return self._get_fallback_content(event_type, context)
            
            template = self._env.get_template(template_path)
            
            # Inject branding into context
            full_context = {
                "doffair_logo": DOFFAIR_LOGO_BASE64,
                "doffair_logo_svg": DOFFAIR_LOGO_SVG,
                "branding_color": BRANDING_COLOR,
                **context
            }
            
            rendered = template.render(**full_context)
            
            logger.debug(f"✅ Rendered template: {template_path}")
            return rendered
            
        except TemplateNotFound as e:
            logger.warning(f"⚠️ Template file not found: {str(e)}")
            return self._get_fallback_content(event_type, context)
        except Exception as e:
            logger.error(f"❌ Failed to render template: {str(e)}")
            return self._get_fallback_content(event_type, context)
    
    def _get_template_path(
        self,
        event_type: EventType,
        recipient_role: RecipientRole,
        channel: NotificationChannel
    ) -> Optional[str]:
        # Handle both enum and string types
        channel_str = channel.value if hasattr(channel, 'value') else str(channel)
        
        if channel_str == "email" or channel == NotificationChannel.EMAIL:
            extension = "email.html"
        elif channel_str == "sms" or channel == NotificationChannel.SMS:
            extension = "sms.txt"
        elif channel_str == "whatsapp" or channel == NotificationChannel.WHATSAPP:
            extension = "whatsapp.txt"
        elif channel_str == "in_app" or channel == NotificationChannel.IN_APP:
            extension = "in_app.txt"
        else:
            return None
        
        event_type_str = event_type.value if hasattr(event_type, 'value') else str(event_type)
        recipient_role_str = recipient_role.value if hasattr(recipient_role, 'value') else str(recipient_role)
        
        template_path = f"{event_type_str}/{recipient_role_str}/{extension}"
        
        full_path = self._templates_dir / event_type_str / recipient_role_str / extension
        if full_path.exists():
            return template_path
        
        return None
    
    def _get_fallback_content(self, event_type: EventType, context: Dict[str, Any]) -> str:
        # Handle both enum and string types
        event_type_str = event_type.value if hasattr(event_type, 'value') else str(event_type)
        event_type_readable = event_type_str.replace("_", " ").title()
        
        fallback = f"{event_type_readable}\n\n"
        
        for key, value in context.items():
            if key not in ['event_id', 'event_type', 'timestamp', 'source']:
                fallback += f"{key.replace('_', ' ').title()}: {value}\n"
        
        return fallback
    
    def template_exists(
        self,
        event_type: EventType,
        recipient_role: RecipientRole,
        channel: NotificationChannel
    ) -> bool:
        template_path = self._get_template_path(event_type, recipient_role, channel)
        if not template_path:
            return False
        
        full_path = self._templates_dir / template_path
        return full_path.exists()


template_renderer = TemplateRenderer()
