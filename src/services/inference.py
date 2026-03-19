"""
Inference Service

Proxies requests to vLLM's OpenAI-compatible API.
This is the bridge between the API gateway and the GPU.
"""

# TODO: Phase 1 - Create InferenceError exception class
#   Fields: message (str), status_code (int, default 502)
#   Used to translate vLLM failures into HTTP errors:
#     502 Bad Gateway = vLLM returned garbage
#     503 Service Unavailable = vLLM is down (ConnectError)
#     504 Gateway Timeout = vLLM took too long (TimeoutException)
#
# TODO: Phase 1 - Create InferenceService class
#   Constructor: takes httpx.AsyncClient (dependency injection)
#
#   Method: async def complete(request: ChatCompletionRequest) -> ChatCompletionResponse
#     1. Convert request to dict with model_dump(exclude_none=True)
#     2. Force stream=False in payload
#     3. POST to "/v1/chat/completions" on the vLLM client
#     4. Handle errors:
#        - httpx.TimeoutException → InferenceError(504)
#        - httpx.ConnectError → InferenceError(503)
#        - Non-200 status → InferenceError(502)
#     5. Parse response JSON into ChatCompletionResponse and return
#
#   Hints:
#     - self._client = http_client (store in constructor)
#     - response = await self._client.post(url, json=payload)
#     - response.json() gives you the parsed dict
#     - ChatCompletionResponse(**data) constructs from dict
