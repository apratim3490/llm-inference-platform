"""
Shared Schema Types

Usage info, error responses, model info - used across multiple endpoints.
These are the building blocks that other schemas compose together.
"""

from pydantic import BaseModel


class UsageInfo(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ErrorResponse(BaseModel):
    error: str
    message: str
    status_code: int

class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    owned_by: str = "local"

class ModelListResponse(BaseModel):
    object: str = "list"
    data: list[ModelInfo]






