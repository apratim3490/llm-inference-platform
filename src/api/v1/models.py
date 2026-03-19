"""
Models Endpoint - GET /v1/models

Lists available models by querying the vLLM backend.
Part of the OpenAI-compatible API surface.
"""

# TODO: Phase 1 - Create GET /models endpoint
#   Steps:
#     1. Get http_client from request.app.state
#     2. GET /v1/models from vLLM
#     3. Parse into ModelListResponse
#     4. If vLLM is unreachable, return empty list (don't crash)
