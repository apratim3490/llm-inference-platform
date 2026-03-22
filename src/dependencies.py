"""
FastAPI Dependency Injection

Provides shared resources to route handlers via FastAPI's Depends() system.

Phase 1: Simple - services are created inline in route handlers.
Phase 2+: Dependencies will be defined here for auth, rate limiting, etc.
"""

# TODO: Phase 2 - Redis client dependency
# TODO: Phase 2 - Auth dependency (current API key)

from fastapi import Request

from src.services.inference import InferenceService


def get_inference_service(request: Request):
    return InferenceService(request.app.state.http_client)

