"""
Chat Completion Request/Response Schemas

Pydantic models matching the OpenAI chat completions format.
Every field is validated automatically - bad requests never reach the GPU.
"""

from time import time
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from src.api.v1.schemas.common import UsageInfo


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = Field(min_length = 1)
    messages: list[ChatMessage] = Field(min_length = 1)
    max_tokens: int = Field(le = 4096, ge = 1, default = 512)
    temperature: float = Field(default = 0.7, le = 2.0, ge = 0.0)
    top_p: float = Field(default = 1.0, le = 1.0, ge = 0.0)
    stream: bool = Field(default = False)
    stop: list[str] | str | None = Field(default = None)

class Choice(BaseModel):
    index: int = Field(default = 0)
    message: ChatMessage
    finish_reason: str | None

class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory = lambda:uuid4().hex[:12])
    object: str = "chat.completion"
    created: int = Field(default_factory= lambda: int(time()))
    model: str
    choices: list[Choice]
    usage: UsageInfo
