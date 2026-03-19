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
