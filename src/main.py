"""
FastAPI Application Factory

Creates and configures the FastAPI app with:
- Lifespan events (startup/shutdown for shared resources)
- Route registration
- Middleware pipeline (added in later phases)
"""

from contextlib import asynccontextmanager

import httpx
import redis.asyncio as aioredis
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.api.router import api_router
from src.config import get_settings
from src.services.inference import InferenceError


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    client = httpx.AsyncClient(base_url=settings.vllm_base_url,
                      timeout=settings.vllm_timeout_seconds)
    redis_client = aioredis.from_url(url = settings.redis_url, decode_responses = True)
    app.state.http_client = client
    app.state.redis_client = redis_client

    yield

    await redis_client.aclose()
    await client.aclose()

def create_app():
    settings = get_settings()
    app = FastAPI(title="LLM Inference Platform", version=settings.version,
                           lifespan=lifespan,
                           docs_url= "/docs" if settings.debug else None)
    app.include_router(api_router)
    return app

app = create_app()

@app.exception_handler(InferenceError)
async def handle_inference_error(request: Request, exception: InferenceError):
    return JSONResponse(status_code = exception.status_code,
                        content = {"error": exception.message})







