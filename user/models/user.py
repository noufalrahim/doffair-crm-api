from datetime import datetime
from typing import Optional
from odmantic import Model, Field


class User(Model):
    """
    User model for customers who use the app
    """
    name: Optional[str] = None
    phone: str = Field(unique=True)
    email: str = Field(unique=True)
    password_hash: str
    
    is_active: bool = True
    is_verified: bool = False
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "collection": "users",
        "indexes": [
            {"fields": ["phone"], "unique": True},
            {"fields": ["email"], "unique": True},
        ],
    }
