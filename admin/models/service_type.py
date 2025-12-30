from datetime import datetime
from typing import Optional, List

from odmantic import Model, Field
from core.enums import ServiceMode


class ServiceType(Model):
    code: str = Field(unique=True)              # grooming, vet, cafe
    display_name: str                           # Pet Grooming
    description: Optional[str] = None           # ← FIXED
    mode: ServiceMode                           # booking | lead
    is_active: bool = True
    image_blob_paths: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "service_types",
         "indexes": [
            {"fields": ["code"], "unique": True},
        ],
    }
