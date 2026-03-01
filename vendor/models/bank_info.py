from odmantic import Model, Field
from typing import Optional
from datetime import datetime

class BankInfo(Model):
    vendor_id: str
    bank_name: str
    account_number: str
    ifsc_code: str
    account_holder_name: str
    branch_name: Optional[str] = None
    is_verified: bool = Field(default=False)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "bank_infos",
        "indexes": [
            {"fields": ["vendor_id"], "unique": True},
        ],
    }
