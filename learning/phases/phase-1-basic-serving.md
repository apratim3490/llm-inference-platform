# Phase 1: Basic Model Serving

## Goal

Get a model running on your RTX 3090 and serve requests through a FastAPI proxy
with OpenAI-compatible endpoints. At the end of this phase, you can `curl` your
API and get chat completions.

## What You'll Learn

- Docker Compose for multi-service orchestration
- vLLM model serving with GPU passthrough
- FastAPI app factory pattern with lifespan events
- Pydantic Settings for environment-based configuration
- OpenAI-compatible API format
- Async HTTP proxying with httpx

## Prerequisites

- WSL2 installed on Windows 11
- NVIDIA Container Toolkit (GPU passthrough for Docker)
- Docker Desktop with WSL2 backend
- Python 3.12

## Concept Docs to Read First

- [01-api-gateway.md](../concepts/01-api-gateway.md)
- [05-model-serving.md](../concepts/05-model-serving.md)

## Steps

### Step 1: WSL2 + GPU Setup

**File**: `scripts/setup_wsl_nvidia.sh`

Verify GPU passthrough works:
```bash
# Inside WSL2
nvidia-smi  # Should show RTX 3090

# Docker GPU test
docker run --gpus all nvidia/cuda:12.1-base nvidia-smi
```

### Step 2: Docker Compose with vLLM

**File**: `docker-compose.yml`

Start with just the vLLM service:
```yaml
services:
  vllm:
    image: vllm/vllm-openai:latest
    ports:
      - "8001:8000"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    command: >
      --model mistralai/Mistral-7B-Instruct-v0.3
      --quantization gptq
      --max-model-len 4096
      --gpu-memory-utilization 0.85
    volumes:
      - model-cache:/root/.cache/huggingface
```

### Step 3: Python Project Scaffolding

**Files**: `pyproject.toml`, `requirements.txt`, `src/__init__.py`, `src/main.py`, `src/config.py`

Key concepts:
- App factory pattern (function that creates and configures the app)
- Lifespan events (setup on startup, cleanup on shutdown)
- Pydantic Settings (config from environment variables)

### Step 4: OpenAI-Compatible Chat Endpoint

**Files**: `src/api/v1/chat.py`, `src/api/v1/schemas/chat.py`, `src/api/v1/schemas/common.py`

Key concepts:
- Pydantic models matching OpenAI's request/response format
- FastAPI route with JSON body parsing
- **`Depends()` for injecting InferenceService** (not created inline)
- **No try/except in endpoints** — global exception handler in `main.py`

Clean pattern:
```python
# src/dependencies.py — define the dependency
async def get_inference_service(request: Request) -> InferenceService:
    return InferenceService(request.app.state.http_client)

# src/api/v1/chat.py — endpoint is clean, no error handling
@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    body: ChatCompletionRequest,
    service: InferenceService = Depends(get_inference_service),
):
    return await service.complete(body)

# src/main.py — global handler catches InferenceError everywhere
@app.exception_handler(InferenceError)
async def inference_error_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.message})
```

### Step 5: Inference Service (Proxy to vLLM)

**File**: `src/services/inference.py`

Key concepts:
- httpx.AsyncClient for non-blocking HTTP
- Connection pooling
- Timeout configuration
- Error mapping (vLLM errors → user-friendly errors)
- Service receives client via constructor (dependency injection)

### Step 6: Router + Models + Health Endpoints

**Files**: `src/api/router.py`, `src/api/v1/models.py`, `src/api/v1/health.py`

Key concepts:
- **Router is pure wiring** — no classes, no logic, just `include_router()` calls
- Models endpoint returns empty list if vLLM unreachable (graceful degradation)
- Health endpoint always returns 200 (liveness only, no dependency checks)

Clean pattern for router:
```python
# src/api/router.py — just wiring, nothing else
api_router = APIRouter()
api_router.include_router(chat_router, prefix="/v1", tags=["chat"])
api_router.include_router(models_router, prefix="/v1", tags=["models"])
api_router.include_router(health_router, tags=["health"])
```

### Step 7: Tests

**Files**: `tests/conftest.py`, `tests/integration/test_chat_endpoint.py`

Key concepts:
- pytest-asyncio for async tests
- httpx.AsyncClient as test client
- respx for mocking HTTP calls to vLLM

## Verification

```bash
# Start the stack
docker compose up -d

# Wait for model to load (~2-5 minutes first time)
curl http://localhost:8001/health

# Test through your gateway
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistralai/Mistral-7B-Instruct-v0.3",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 50
  }'
```

Expected: A JSON response with the model's reply.

## Files Created This Phase

```
src/
├── __init__.py
├── main.py              ← FastAPI app factory + lifespan
├── config.py            ← Pydantic Settings
├── dependencies.py      ← Dependency injection
├── api/
│   ├── __init__.py
│   ├── router.py        ← Route aggregation
│   └── v1/
│       ├── __init__.py
│       ├── chat.py      ← POST /v1/chat/completions
│       ├── models.py    ← GET /v1/models
│       └── schemas/
│           ├── __init__.py
│           ├── chat.py  ← Request/Response Pydantic models
│           └── common.py ← Shared types (Usage, Error)
└── services/
    ├── __init__.py
    └── inference.py     ← Proxy to vLLM
```

## What's Next?

Phase 2 adds authentication, rate limiting, and usage tracking. Right now,
anyone can hit your API with no limits - Phase 2 fixes that.
