"""
Models Endpoint - GET /v1/models

Lists available models by querying the vLLM backend.
Part of the OpenAI-compatible API surface.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from src.dependencies import get_inference_service
from src.services.inference import InferenceService

router = APIRouter()

@router.get("/models")
async def get_models(service: InferenceService =
                            Depends(get_inference_service)) -> JSONResponse:
    return await service.list_models()
