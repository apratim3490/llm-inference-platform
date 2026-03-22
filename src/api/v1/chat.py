"""
Chat Completions Endpoint - POST /v1/chat/completions

The core endpoint. Accepts OpenAI-format requests, proxies to vLLM,
returns the response. Any OpenAI SDK client works with this.
"""

from fastapi import APIRouter, Depends

from src.api.v1.schemas.chat import ChatCompletionRequest, ChatCompletionResponse
from src.dependencies import get_inference_service
from src.services.inference import InferenceService

router = APIRouter()

@router.post("/chat/completions")
async def invoke_completion(body: ChatCompletionRequest,
                            service: InferenceService =
                            Depends(get_inference_service)) -> ChatCompletionResponse:
    return await service.complete(body)

