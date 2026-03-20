# Phase 6: Production Hardening

## Goal

Make the system resilient to failures. Add health checks, circuit breaker,
SSL termination via nginx, graceful shutdown, and proper error handling.

## What You'll Learn

- Liveness vs readiness probes (Kubernetes pattern)
- Circuit breaker state machine (CLOSED/OPEN/HALF_OPEN)
- Graceful shutdown with in-flight request draining
- nginx as reverse proxy with SSL
- Timeout chains (inner < outer)
- Global error handling (never leak stack traces)

## Concept Docs to Read First

- [09-circuit-breaker.md](../concepts/09-circuit-breaker.md)
- [11-health-checks.md](../concepts/11-health-checks.md)

## Clean Approach Notes

- **Circuit breaker wraps InferenceService**, doesn't modify it. Use the wrapper
  pattern to keep InferenceService clean and testable on its own.
- **Global error handler already exists** from Phase 1 (`main.py` exception handlers).
  Phase 6 expands it to catch all unhandled exceptions → 500 with no stack traces.
- **`/health` stays simple** (always 200). All dependency-checking logic goes in `/ready`.

## Steps

### Step 1: Health Checks
**File**: `src/observability/health.py`, `src/api/v1/health.py`

/health (liveness — always 200) and /ready (readiness with dependency checks).

### Step 2: Circuit Breaker (Wrapper Pattern)
**File**: `src/services/circuit_breaker.py`

Clean pattern — wraps InferenceService, doesn't modify it:
```python
class CircuitBreakerService:
    def __init__(self, service: InferenceService, breaker: CircuitBreaker):
        self._service = service
        self._breaker = breaker

    async def complete(self, request):
        if self._breaker.is_open:
            raise InferenceError("Service unavailable", 503)
        try:
            result = await self._service.complete(request)
            self._breaker.record_success()
            return result
        except InferenceError:
            self._breaker.record_failure()
            raise
```

### Step 3: Graceful Shutdown
**File**: `src/main.py`

On SIGTERM: stop accepting, drain queue, close connections, exit.
This extends the existing lifespan shutdown logic.

### Step 4: nginx Reverse Proxy
**Files**: `docker-compose.yml`, `config/nginx/nginx.conf`

SSL termination, request buffering, connection limits.

### Step 5: Timeout Enforcement
Layered timeouts: global (120s) > vLLM call (90s) > queue wait (30s).

### Step 6: Expand Global Error Handler
**File**: `src/main.py`

Extend the exception handlers from Phase 1 to catch all unhandled exceptions:
```python
@app.exception_handler(Exception)
async def unhandled_error(request, exc):
    logger.error("unhandled_exception", exc_info=exc)
    return JSONResponse(status_code=500, content={"error": "Internal server error"})
```
Never leak stack traces to clients.

### Step 7: Tests
Circuit breaker state transitions, health responses with backends down/up.

## Verification

```bash
# Health check
curl http://localhost:8000/health   # → 200 always
curl http://localhost:8000/ready    # → 200 when all deps up, 503 when vLLM down

# Stop vLLM, send requests
docker compose stop vllm
curl -X POST http://localhost:8000/v1/chat/completions ...
# → 503 immediately (circuit breaker) instead of 90s timeout

# Restart vLLM, wait 30s, requests work again
docker compose start vllm
```
