"""
FastAPI Dependency Injection

Provides shared resources to route handlers via FastAPI's Depends() system.

Phase 1: Simple - services are created inline in route handlers.
Phase 2+: Dependencies will be defined here for auth, rate limiting, etc.
"""

import hashlib
from typing import cast

import httpx
from fastapi import Depends, HTTPException, Request
from redis.asyncio import Redis

from src.models.api_key import APIKey
from src.models.enums import Tier
from src.services.inference import InferenceService


def get_inference_service(request: Request) -> InferenceService:
    return InferenceService(cast(httpx.AsyncClient, request.app.state.http_client))

def get_redis(request: Request) -> Redis:
    return cast(Redis, request.app.state.redis_client)

async def require_auth(request: Request, redis: Redis = Depends(get_redis)) -> APIKey:
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401,
                            detail="Missing or invalid authorization header")

    token = auth_header.removeprefix("Bearer ")
    key_hash = hashlib.sha256(token.encode()).hexdigest()
    key_data: dict[str, str] = await redis.hgetall(f"apikey:{key_hash}") # type: ignore[misc]
    if not key_data:
        raise HTTPException(status_code=401, detail="Invalid API key")

    api_key = APIKey(
        key_hash=key_hash,
        name=key_data["name"], # type: ignore[misc]
        tier=Tier(key_data["tier"]),
        rpm_limit=int(key_data["rpm_limit"]), # type: ignore[misc]
        tpm_limit=int(key_data["tpm_limit"]), # type: ignore[misc]
        is_active=key_data.get("is_active", "true").lower() == "true" # type: ignore[misc]
    )

    if not api_key.is_active:
        raise HTTPException(status_code=403, detail="API key has been deactivated")

    return api_key

