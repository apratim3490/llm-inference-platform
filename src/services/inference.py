"""
Inference Service

Proxies requests to vLLM's OpenAI-compatible API.
This is the bridge between the API gateway and the GPU.
"""

import httpx

from src.api.v1.schemas.chat import ChatCompletionRequest, ChatCompletionResponse
from src.config import get_settings


class InferenceError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class InferenceService:
    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self._settings = get_settings()
        self._client = http_client

    async def complete(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        try:
            payload = request.model_dump(exclude_none = True)
            payload["stream"] = False
            response = await self._client.post(self._settings.completion_url, json = payload)
        except httpx.TimeoutException:
            raise InferenceError("vLLM timed out", 504)
        except httpx.ConnectError:
            raise InferenceError("vLLM Unavailable", 503)

        if response.status_code != 200:
            raise InferenceError(f"vLLM returned {response.status_code}", 502)

        data = response.json()
        return ChatCompletionResponse(**data)





