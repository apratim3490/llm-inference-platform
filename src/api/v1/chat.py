"""
Chat Completions Endpoint - POST /v1/chat/completions

The core endpoint. Accepts OpenAI-format requests, proxies to vLLM,
returns the response. Any OpenAI SDK client works with this.
"""

# TODO: Phase 1 - Create router (APIRouter from fastapi)
#
# TODO: Phase 1 - Create POST /chat/completions endpoint
#   Function signature: async def create_chat_completion(body: ChatCompletionRequest, request: Request)
#
#   Steps:
#     1. Get http_client from request.app.state.http_client
#     2. Create InferenceService with the client
#     3. Call service.complete(body)
#     4. Catch InferenceError → return JSONResponse with error details
#     5. Return the ChatCompletionResponse on success
#
#   Hints:
#     - body: ChatCompletionRequest auto-parses and validates the JSON body
#     - request: Request gives access to app.state
#     - Use @router.post("/chat/completions", response_model=ChatCompletionResponse)
#     - JSONResponse(status_code=..., content={...}) for error responses

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from src.api.v1.schemas.chat import ChatCompletionRequest, ChatCompletionResponse
from src.services.inference import InferenceError, InferenceService

router = APIRouter()

@router.post("/chat/completions")
async def invoke_completion(request: Request,
                            body: ChatCompletionRequest
                            ) -> ChatCompletionResponse | JSONResponse:
    client = request.app.state.http_client
    inference_service = InferenceService(client)
    try:
        response = await inference_service.complete(body)
    except InferenceError as e:
        return JSONResponse(content={"error": e.message}, status_code = e.status_code)

    return response
