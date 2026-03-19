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

## Steps

### Step 1: Health Checks
**File**: `src/observability/health.py`, `src/api/v1/health.py`

/health (liveness) and /ready (readiness with dependency checks).

### Step 2: Circuit Breaker
**File**: `src/services/circuit_breaker.py`

Three-state circuit breaker: CLOSED → OPEN → HALF_OPEN. Threshold-based triggering.

### Step 3: Graceful Shutdown
**File**: `src/main.py`

On SIGTERM: stop accepting, drain queue, close connections, exit.

### Step 4: nginx Reverse Proxy
**Files**: `docker-compose.yml`, `config/nginx/nginx.conf`

SSL termination, request buffering, connection limits.

### Step 5: Timeout Enforcement
Layered timeouts: global (120s) > vLLM call (90s) > queue wait (30s).

### Step 6: Global Error Handler
**File**: `src/middleware/error_handler.py`

Catch all exceptions → clean JSON errors. Never leak stack traces.

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
