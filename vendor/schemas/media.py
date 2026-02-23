from pydantic import BaseModel
from typing import List


class ImageResponseSchema(BaseModel):
    status: str
    paths: List[str]


class MessageResponse(BaseModel):
    status: str
