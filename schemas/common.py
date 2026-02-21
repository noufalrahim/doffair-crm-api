from typing import Any, Optional
from pydantic import BaseModel


class APIResponse(BaseModel):
    success: bool
    success_message: Optional[str] = None
    error_message: Optional[str] = None
    data: Optional[Any] = None
    meta: Optional[dict] = None
