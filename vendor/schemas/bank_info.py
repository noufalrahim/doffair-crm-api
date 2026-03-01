from pydantic import BaseModel, Field
from typing import Optional, TypeVar, Generic
from datetime import datetime
from schemas.common import APIResponse

class BankInfoCreateRequest(BaseModel):
    bank_name: str = Field(..., example="HDFC Bank")
    account_number: str = Field(..., example="50100123456789")
    ifsc_code: str = Field(..., example="HDFC0001234")
    account_holder_name: str = Field(..., example="John Doe")
    branch_name: Optional[str] = Field(None, example="Downtown Branch")

class BankInfoUpdateRequest(BaseModel):
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    account_holder_name: Optional[str] = None
    branch_name: Optional[str] = None

class BankInfoResponse(BaseModel):
    id: str
    vendor_id: str
    bank_name: str
    account_number: str
    ifsc_code: str
    account_holder_name: str
    branch_name: Optional[str] = None
    is_verified: bool
    created_at: datetime
    updated_at: datetime

T = TypeVar("T")

class GenericAPIResponse(APIResponse, Generic[T]):
    data: Optional[T] = None

class BankInfoAPIResponse(GenericAPIResponse[BankInfoResponse]):
    pass
