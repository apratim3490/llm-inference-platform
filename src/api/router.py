"""
Top-Level Router Aggregation

Collects all versioned API routers and mounts them.
"""

from fastapi import APIRouter

from src.api.v1.chat import router as chat_router
from src.api.v1.health import router as healthcheck_router
from src.api.v1.models import router as models_router

api_router = APIRouter()
api_router.include_router(chat_router, prefix="/v1", tags=["chat"])
api_router.include_router(healthcheck_router, prefix = "", tags = ["healthcheck"])
api_router.include_router(models_router, prefix = "/v1", tags = ["models"])



