from datetime import datetime
from odmantic import Model, Field # type: ignore


class Admin(Model):
    email: str = Field(unique=True)
    password_hash: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "admins"
    }
