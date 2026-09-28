from pydantic import BaseModel
from typing import Any, Optional

class Meta(BaseModel):
    total: Optional[int] = None
    page: Optional[int] = None
    per_page: Optional[int] = None

class ErrorDetail(BaseModel):
    code: int
    message: str
    details: Optional[Any] = None

class APIResponse(BaseModel):
    data: Any = None
    meta: Optional[Meta] = None
    error: Optional[ErrorDetail] = None
