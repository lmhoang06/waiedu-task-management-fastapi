from typing import Any, Optional
from pydantic import BaseModel

class ErrorDetail(BaseModel):
    code: str
    details: str

class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[ErrorDetail] = None
    message: str

class ForgotPasswordRequestIn(BaseModel):
    username: str | None = None
    email: str | None = None
    full_name: str
    new_password: str