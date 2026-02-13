from datetime import datetime
from typing import Optional, List

from odmantic import Model, Field
from core.enums import ServiceMode


class Vertical(Model):
    code: List[str] = Field(unique=True)        # ['groomer', 'groom', 'grooming']
    display_name: str                           # Pet Grooming
    description: Optional[str] = None           # ← FIXED
    mode: ServiceMode                           # booking | lead
    is_active: bool = True
    image_blob_paths: List[str] = []
    url: Optional[str] = None
    icon: Optional[str] = None
    priority: int = 100
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "verticals",
         "indexes": [
            {"fields": ["code"], "unique": True},
        ],
    }
