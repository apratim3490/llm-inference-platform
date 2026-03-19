# Your Local Build vs. Frontier AI Lab

This document maps every component you build to what companies like Anthropic,
OpenAI, and Google DeepMind run in production. The concepts are identical -
only the scale differs.

## Side-by-Side Comparison

### API Gateway

| Yours | Frontier Lab |
|-------|-------------|
| 1 FastAPI process on your PC | Fleet of hundreds of API gateway pods |
| Single-threaded async | Load-balanced across multiple data centers |
| nginx reverse proxy | Global anycast CDN (Cloudflare, custom) |
| JSON validation with Pydantic | Same pattern, often with protobuf schemas |

**What scales**: Number of gateway instances, geographic distribution.
**What stays the same**: The validation logic, middleware pipeline, OpenAI-compatible format.

### Authentication

| Yours | Frontier Lab |
|-------|-------------|
| API keys stored in Redis | API keys in distributed database + cache |
| SHA-256 hash lookup | Same hashing, plus org-level permissions, OAuth, SSO |
| 3 tiers (free/pro/admin) | Complex tier system with custom rate limits per customer |
| Manual key generation script | Self-service dashboard, team management, billing integration |

**What scales**: Number of keys (millions), permission complexity, audit logging.
**What stays the same**: Bearer token pattern, hash-then-lookup, tier-based limits.

### Rate Limiting

| Yours | Frontier Lab |
|-------|-------------|
| Token bucket in Redis (Lua) | Same algorithm, distributed across Redis Cluster |
| RPM + TPM per key | RPM + TPM + concurrent requests + daily limits + org-level limits |
| Single Redis instance | Redis Cluster or custom distributed counter |
| 429 + Retry-After header | Same, plus rate limit headers (x-ratelimit-remaining) |

**What scales**: Number of counters, geographic consistency (eventual vs strong).
**What stays the same**: Token bucket algorithm, Lua atomicity, HTTP 429 pattern.

### Request Queue

| Yours | Frontier Lab |
|-------|-------------|
| Redis sorted set, 3 priorities | Kafka or custom queue, many priority levels |
| Max 100 queued requests | Millions of requests in queue |
| Single consumer (asyncio) | Thousands of consumer workers across GPU clusters |
| Simple FIFO within priority | Sophisticated scheduling (fair queuing, SLO-based) |

**What scales**: Queue depth, number of consumers, scheduling sophistication.
**What stays the same**: Priority ordering, FIFO within priority, backpressure (503 when full).

### Model Serving

| Yours | Frontier Lab |
|-------|-------------|
| 1 RTX 3090, 24GB VRAM | Thousands of H100/B200 GPUs, 80GB+ VRAM each |
| 1 model (Mistral 7B) | Multiple models (Claude 4, Haiku, Opus), multiple versions |
| vLLM continuous batching | Custom serving stack (TensorRT-LLM, custom kernels) |
| ~8-16 concurrent requests | Thousands of concurrent requests per cluster |
| 4-bit quantization | FP8/FP16 or custom precision, tensor parallelism across GPUs |

**What scales**: Number of GPUs, model size (70B→400B+), parallelism strategy.
**What stays the same**: Continuous batching concept, KV cache management, PagedAttention-like ideas.

### Streaming (SSE)

| Yours | Frontier Lab |
|-------|-------------|
| FastAPI StreamingResponse | Same pattern at edge, proxied through CDN |
| SSE format (data: {...}\n\n) | Identical SSE format (OpenAI standard) |
| Client disconnect detection | Same, plus WebSocket support for some APIs |
| Single connection | Connection pooling, HTTP/2 multiplexing |

**What scales**: Number of concurrent streams, edge caching strategy.
**What stays the same**: SSE protocol, chunk format, disconnect detection. This is basically identical.

### Usage Tracking

| Yours | Frontier Lab |
|-------|-------------|
| Redis counters per key per day | Time-series database (ClickHouse, BigQuery) |
| Token counts (in + out) | Token counts + compute time + features used |
| Simple accumulation | Real-time billing pipeline, invoicing, spend alerts |
| JSON records in Redis | Event stream → data warehouse → billing system |

**What scales**: Data volume, query complexity, billing integration.
**What stays the same**: Count every token, attribute to a key, aggregate by time period.

### Safety Layer

| Yours | Frontier Lab |
|-------|-------------|
| Keyword blocklist + regex | Multi-model classifier pipeline |
| Optional small CPU classifier | Dedicated safety models running on separate GPUs |
| Binary safe/unsafe | Risk scores, categories, confidence levels, human review queues |
| Pre and post filtering | Same, plus Constitutional AI, RLHF, model-level safety |

**What scales**: Model sophistication, number of safety classifiers, human review capacity.
**What stays the same**: Pre-inference + post-inference filtering, category-based blocking.

### Circuit Breaker

| Yours | Frontier Lab |
|-------|-------------|
| In-process Python class | Service mesh (Istio/Envoy) circuit breakers |
| 3 states, simple thresholds | Same 3 states, sophisticated health scoring |
| Protects 1 backend (vLLM) | Protects every service-to-service connection |
| Manual recovery | Auto-recovery with gradual traffic ramp-up |

**What scales**: Number of services protected, sophistication of health checks.
**What stays the same**: CLOSED/OPEN/HALF_OPEN state machine, fast-fail pattern.

### Observability

| Yours | Frontier Lab |
|-------|-------------|
| Prometheus + Grafana (Docker) | Prometheus/Cortex/Mimir at massive scale |
| 3 dashboards | Hundreds of dashboards, custom alerting |
| structlog JSON to stdout | Centralized logging (ELK, ClickHouse, Datadog) |
| Manual dashboard inspection | PagerDuty alerts, automated incident response |
| Request IDs for correlation | Distributed tracing (Jaeger, OpenTelemetry) |

**What scales**: Data volume, alerting sophistication, trace depth.
**What stays the same**: Prometheus metrics types, PromQL, structured logging format, request ID correlation.

### Health Checks

| Yours | Frontier Lab |
|-------|-------------|
| /health + /ready endpoints | Identical endpoints, consumed by Kubernetes |
| Check Redis + vLLM status | Check dozens of dependencies |
| Manual monitoring | Kubernetes auto-restarts unhealthy pods |
| Simple up/down status | Detailed health scores per dependency |

**What scales**: Number of dependencies checked, automated remediation.
**What stays the same**: Liveness vs readiness distinction, HTTP endpoint pattern.

### Internet Exposure

| Yours | Frontier Lab |
|-------|-------------|
| Cloudflare Tunnel | Global anycast CDN with custom edge logic |
| 1 origin server | Hundreds of origin servers across regions |
| Cloudflare DDoS protection | Custom DDoS mitigation + WAF + bot detection |
| Single domain | Multiple domains, API versioning at edge |

**What scales**: Geographic distribution, edge computing, traffic volume.
**What stays the same**: SSL termination, DDoS protection, reverse proxy pattern.

## The Key Insight

> The architecture patterns are the same at every scale. What changes is the
> number of instances, the sophistication of each component, and the operational
> complexity. By building this locally, you understand the WHY behind every
> component - which is the knowledge that matters most.

When you interview at a frontier AI lab and they ask "how would you design an
inference API?", you won't just recite an architecture diagram - you'll have
BUILT one. You'll know that the rate limiter uses Lua scripts because Redis
needs atomic check-and-decrement. You'll know that circuit breakers need a
HALF_OPEN state because you have to probe recovery. You'll know that SSE
streaming needs client disconnect detection because wasted GPU cycles cost money.

That's the difference between knowing the map and having walked the territory.
