from pydantic import BaseModel
from typing import Optional, List
from vendor.schemas.booking import PetSummary

class CustomerPetDiscoveryResponse(BaseModel):
    id: Optional[str] = None
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    pet: Optional[PetSummary] = None
