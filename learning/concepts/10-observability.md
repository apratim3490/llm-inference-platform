# Concept: Observability

## What Is It?

Observability is the ability to understand what your system is doing from the
outside by examining its outputs: metrics, logs, and traces. It's the difference
between "something is broken" and "the p99 latency on /v1/chat/completions
increased by 3x at 2:14pm because the KV cache hit 90% utilization."

## The Three Pillars

### 1. Metrics (Prometheus)
Numbers that tell you HOW MUCH and HOW FAST:
- Request rate: 42 requests/minute
- Error rate: 2.3% of requests failed
- Latency p95: 1.2 seconds
- GPU utilization: 78%
- Queue depth: 12 requests waiting

### 2. Logs (structlog)
Events that tell you WHAT HAPPENED:
```json
{
  "timestamp": "2026-03-18T14:30:00Z",
  "level": "info",
  "request_id": "req_a1b2c3d4",
  "event": "request_completed",
  "method": "POST",
  "path": "/v1/chat/completions",
  "status": 200,
  "latency_ms": 890,
  "input_tokens": 127,
  "output_tokens": 89,
  "api_key_tier": "pro"
}
```

### 3. Traces (Request IDs)
The thread that connects events across components:
```
req_a1b2c3d4 → auth_check (1ms) → rate_limit (1ms) → queue_wait (50ms)
             → inference (800ms) → safety_check (5ms) → response_sent
```

## Prometheus Metrics Types

### Counter (always goes up)
```python
requests_total = Counter(
    "requests_total",
    "Total requests",
    ["method", "endpoint", "status", "tier"]
)
# Usage: requests_total.labels("POST", "/v1/chat/completions", "200", "pro").inc()
```
Good for: request counts, error counts, token totals

### Histogram (distribution of values)
```python
request_duration = Histogram(
    "request_duration_seconds",
    "Request latency",
    ["endpoint"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)
# Usage: request_duration.labels("/v1/chat/completions").observe(0.89)
```
Good for: latency, TTFT, token generation rate
Gives you: p50, p90, p95, p99 automatically

### Gauge (goes up and down)
```python
queue_depth = Gauge(
    "queue_depth",
    "Current queue size",
    ["priority"]
)
# Usage: queue_depth.labels("P1").set(12)
```
Good for: queue depth, active connections, GPU memory

## Your Metrics

| Metric | Type | Labels | Why |
|--------|------|--------|-----|
| `request_duration_seconds` | Histogram | endpoint, status | Overall latency |
| `time_to_first_token_seconds` | Histogram | model | Streaming UX quality |
| `requests_total` | Counter | endpoint, status, tier | Traffic volume |
| `tokens_processed_total` | Counter | model, direction, tier | Usage/cost tracking |
| `queue_depth` | Gauge | priority | Backpressure signal |
| `active_requests` | Gauge | - | Concurrency monitoring |
| `vllm_backend_healthy` | Gauge | - | Backend health (0 or 1) |
| `rate_limit_rejections_total` | Counter | tier, limit_type | Rate limit effectiveness |
| `safety_filter_triggers_total` | Counter | direction, category | Safety layer activity |

## Grafana Dashboards

### Inference Overview Dashboard
```
┌────────────────────┬────────────────────┬────────────────────┐
│ Request Rate       │ Error Rate         │ p95 Latency        │
│ 42 req/min    ↑3%  │ 2.3%         ↑0.1% │ 1.2s          ↓5%  │
├────────────────────┴────────────────────┴────────────────────┤
│ Latency Distribution (last 1h)                               │
│ ██████████████████████████████████████░░░░░░  p50: 0.4s      │
│ ██████████████████████████████████████████░░  p95: 1.2s      │
│ ████████████████████████████████████████████  p99: 2.8s      │
├────────────────────┬────────────────────┬────────────────────┤
│ TTFT Distribution  │ Tokens/Second      │ Queue Depth        │
│ p50: 180ms         │ 145 tok/s     ↑2%  │ P0: 0  P1: 3  P2: │
└────────────────────┴────────────────────┴────────────────────┘
```

## Why Structured Logging?

**Unstructured** (useless at scale):
```
INFO 2026-03-18 14:30:00 Request completed in 890ms
```

**Structured** (searchable, parseable):
```json
{"level":"info","timestamp":"2026-03-18T14:30:00Z","event":"request_completed","latency_ms":890,"request_id":"req_a1b2"}
```

With structured logs, you can:
- `jq '.[] | select(.latency_ms > 2000)'` → find slow requests
- `jq '.[] | select(.request_id == "req_a1b2")'` → trace one request
- Feed into any log aggregation tool (ELK, ClickHouse, Datadog)

## Files You'll Build

| File | Purpose |
|------|---------|
| `src/observability/metrics.py` | Prometheus metric definitions |
| `src/observability/logging_config.py` | structlog JSON configuration |
| `src/observability/health.py` | Health check logic |
| `src/middleware/logging_middleware.py` | Per-request structured logging |
| `config/prometheus/prometheus.yml` | Scrape configuration |
| `config/grafana/dashboards/*.json` | Dashboard definitions |
