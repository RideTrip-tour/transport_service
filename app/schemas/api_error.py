from typing import Any

from pydantic import BaseModel, Field


class ApiErrorResponse(BaseModel):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    details: dict[str, Any] | None = None
    trace_id: str

