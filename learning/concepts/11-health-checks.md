# Concept: Health Checks

## What Is It?

Health checks are endpoints that report whether your service is alive and ready
to handle requests. They're the heartbeat of production systems - monitoring
tools, load balancers, and orchestrators (Kubernetes) constantly ping them.

## Why Does It Exist?

Without health checks:
- Load balancer sends traffic to a dead instance → users get errors
- You don't know vLLM crashed until users complain
- No automated recovery is possible
- Deployment rollouts can't verify the new version works

## Two Types (Kubernetes Pattern)

### Liveness Probe: GET /health
**Question**: "Is the process alive?"

```json
// Healthy
{"status": "healthy"}  // HTTP 200

// Unhealthy (process is hung/deadlocked)
// → No response (timeout) → Restart the process
```

This check is cheap: if FastAPI can respond at all, it's alive. The liveness
probe should NEVER check dependencies (Redis, vLLM). A slow Redis shouldn't
cause your process to restart.

### Readiness Probe: GET /ready
**Question**: "Can this instance handle requests right now?"

```json
// Ready
{
  "status": "ready",
  "checks": {
    "redis": {"status": "up", "latency_ms": 1},
    "vllm": {"status": "up", "latency_ms": 45},
    "gpu": {"status": "available", "memory_used_pct": 72}
  }
}  // HTTP 200

// Not ready
{
  "status": "not_ready",
  "checks": {
    "redis": {"status": "up", "latency_ms": 1},
    "vllm": {"status": "down", "error": "connection refused"},
    "gpu": {"status": "unknown"}
  }
}  // HTTP 503
```

If the readiness probe returns 503:
- Load balancer stops sending traffic to this instance
- Existing in-flight requests can finish
- Once the probe returns 200 again, traffic resumes

## Real-World Analogy

**Liveness**: "Is the restaurant open?" (lights on, door unlocked)
**Readiness**: "Can the restaurant serve food?" (chef is present, kitchen is stocked)

A restaurant can be open (alive) but unable to serve food (not ready) if the
chef called in sick. You wouldn't close the restaurant (restart) - you'd just
stop seating new customers (stop routing traffic) until the chef arrives.

## What Gets Checked

| Dependency | How to Check | Failure Means |
|------------|-------------|---------------|
| Redis | `PING` command | Rate limiting and queue broken |
| vLLM | `GET /health` on :8001 | Can't generate responses |
| GPU | Check vLLM GPU metrics | Model may OOM |
| Disk | Check log directory writable | Logging may fail |

## Files You'll Build

| File | Purpose |
|------|---------|
| `src/observability/health.py` | Health check logic for all dependencies |
| `src/api/v1/health.py` | /health and /ready endpoint handlers |
| `tests/integration/test_health.py` | Test responses with backends up and down |
