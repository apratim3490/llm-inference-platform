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

## Steps

### Step 1: Define Prometheus Metrics
**File**: `src/observability/metrics.py`

All metric definitions in one place: request duration, TTFT, token counts, queue depth, etc.

### Step 2: Instrument All Components
**Files**: All middleware and service files

Add timing and counting instrumentation to auth, rate limiter, inference, queue, safety.

### Step 3: Structured Logging
**File**: `src/observability/logging_config.py`

Configure structlog with JSON output, request_id context, masked API keys.

### Step 4: Logging Middleware
**File**: `src/middleware/logging_middleware.py`

Log every request start and completion with method, path, status, latency, tokens.

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
