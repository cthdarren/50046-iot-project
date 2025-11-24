from pydantic import BaseModel
from typing import Any, Optional

class APIError(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None

class SuccessResponse(BaseModel):
    success: bool = True
    data: Any

class ErrorResponse(BaseModel):
    success: bool = False
    error: APIError
    