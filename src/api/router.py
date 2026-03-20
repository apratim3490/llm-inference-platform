"""
Top-Level Router Aggregation

Collects all versioned API routers and mounts them.
"""

# TODO: Phase 1 - Create api_router (APIRouter)
#   - Include health_router at root level (no prefix) with tags=["health"]
#   - Include chat_router under prefix="/v1" with tags=["chat"]
#   - Include models_router under prefix="/v1" with tags=["models"]
#
#   Hint: router.include_router(other_router, prefix="/v1", tags=["chat"])
#   The prefix means /chat/completions becomes /v1/chat/completions

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from src.services.inference import InferenceError, InferenceService

class ApiRouter(APIRouter):

    def __init__(self, inference_service: InferenceService):
        self._inference_service = inference_service

    




