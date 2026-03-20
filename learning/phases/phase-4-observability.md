# Phase 4: Observability

## Goal

Full observability stack: Prometheus metrics, Grafana dashboards, and structured
JSON logging. After this phase, you can see exactly what your system is doing
in real-time through dashboards.

## What You'll Learn

- Prometheus metric types (Counter, Histogram, Gauge)
- Instrumenting application code with metrics
- structlog for structured JSON logging
- Grafana dashboard creation
- Prometheus scraping and PromQL basics
- Correlation with request IDs across logs and metrics

## Concept Docs to Read First

- [10-observability.md](../concepts/10-observability.md)

## Clean Approach Notes

- **Metrics defined once, imported everywhere.** Never create metrics inline in
  service code. One `metrics.py` file is the single source of truth.
- **`structlog` with bound loggers**, not Python's built-in `logging`. Bind
  `request_id` once per request, then every subsequent log call includes it.
- **Logging middleware IS appropriate as middleware** — unlike auth, it genuinely
  runs on every request. Use `time.perf_counter()` for latency, not `time.time()`.

## Steps

### Step 1: Define Prometheus Metrics
**File**: `src/observability/metrics.py`

All metric definitions in one place: request duration, TTFT, token counts, queue depth, etc.

### Step 2: Instrument All Components
**Files**: All service files

Add timing and counting instrumentation to inference, queue, safety.
Clean pattern: services call `metric.observe()` / `metric.inc()` directly.

### Step 3: Structured Logging
**File**: `src/observability/logging_config.py`

Configure structlog with JSON output (production) or pretty-print (development).
Clean pattern — bound loggers:
```python
logger = structlog.get_logger()
log = logger.bind(request_id=request_id, path=path)
log.info("request_started")
log.info("request_completed", status=200, latency_ms=45)
```

### Step 4: Logging Middleware
**File**: `src/middleware/logging_middleware.py`

Log every request start and completion with method, path, status, latency, tokens.
Use `time.perf_counter()` for accurate latency measurement.

### Step 5: Prometheus + Grafana in Docker Compose
**Files**: `docker-compose.yml`, `config/prometheus/prometheus.yml`

Add containers, configure scraping of FastAPI and vLLM metrics endpoints.

### Step 6: Grafana Dashboards
**Files**: `config/grafana/dashboards/*.json`

Three dashboards: Inference Overview, GPU Utilization, Usage & Billing.

### Step 7: Tests

Verify metrics increment correctly, health endpoint exposes Prometheus format.

## Verification

- Visit `http://localhost:3000` (Grafana) → see live dashboards
- Visit `http://localhost:8000/metrics` → see Prometheus metrics
- Check container logs → see structured JSON with request IDs
- Make a few requests → watch metrics change in real-time

## Files Created This Phase

```
src/
├── observability/
│   ├── __init__.py
│   ├── metrics.py           ← Prometheus definitions
│   ├── logging_config.py    ← structlog JSON config
│   └── health.py            ← Health check logic
├── middleware/
│   └── logging_middleware.py ← Per-request logging

config/
├── prometheus/
│   └── prometheus.yml       ← Scrape config
└── grafana/
    ├── provisioning/...     ← Auto-provisioning
    └── dashboards/
        ├── inference-overview.json
        ├── gpu-utilization.json
        └── usage-billing.json
```
