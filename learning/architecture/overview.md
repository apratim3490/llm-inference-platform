# Architecture Overview

## The System You're Building

```
                            INTERNET
                               |
                    [Cloudflare Tunnel]
                               |
                         ┌─────┴──────┐
                         │   nginx    │  SSL termination
                         │            │  reverse proxy
                         └─────┬──────┘
                               │ :443 → :8000
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                     FastAPI API Gateway (:8000)                   │
│                                                                  │
│  Request arrives → gets a unique ID → auth check → rate limit   │
│  → input safety check → joins queue → sent to model → output    │
│  safety check → usage tracked → response sent back              │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Middleware Pipeline (in order)                │   │
│  │                                                           │   │
│  │  1. Request ID    → Every request gets a UUID             │   │
│  │  2. Auth          → Is this API key valid?                │   │
│  │  3. Rate Limiter  → Has this key exceeded its limits?     │   │
│  │  4. Validation    → Is the request format correct?        │   │
│  │  5. Safety Filter → Is the input content safe?            │   │
│  │  6. Router        → Send to the right handler             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌──────────────────────────┴───────────────────────────────┐   │
│  │                   Request Queue                           │   │
│  │                                                           │   │
│  │   Priority 0 (admin)  ████░░░░░░  → served first         │   │
│  │   Priority 1 (pro)    ██████░░░░  → served second         │   │
│  │   Priority 2 (free)   ████████░░  → served last           │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                              │                                   │
│  ┌──────────────────────────┴───────────────────────────────┐   │
│  │              Inference Service (proxy to vLLM)            │   │
│  │                                                           │   │
│  │  Non-streaming: wait for full response, return JSON       │   │
│  │  Streaming: yield tokens one-by-one as SSE events         │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                              │                                   │
│  ┌──────────────────────────┴───────────────────────────────┐   │
│  │              Usage Tracker                                │   │
│  │                                                           │   │
│  │  Count input tokens + output tokens per request           │   │
│  │  Accumulate daily totals per API key                      │   │
│  │  This is the foundation of billing                        │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────┼───────────────────────────────────┘
                               │ HTTP
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                    vLLM Model Server (:8001)                      │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Continuous Batching Engine                                 │  │
│  │                                                             │  │
│  │  Instead of processing one request at a time, vLLM groups  │  │
│  │  multiple requests together and processes them in parallel  │  │
│  │  on the GPU. This is like a bus vs individual taxis.        │  │
│  │                                                             │  │
│  │  PagedAttention: Manages GPU memory like an OS manages     │  │
│  │  RAM - using "pages" so multiple requests can share the    │  │
│  │  GPU without wasting memory.                               │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────┐                                              │
│  │  RTX 3090      │  Mistral 7B (4-bit): ~4GB weights            │
│  │  24GB VRAM     │  Remaining ~18GB: KV cache for 8-16 users    │
│  └────────────────┘                                              │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    Observability Stack                            │
│                                                                  │
│  Prometheus (:9090)     ← Scrapes metrics every 15 seconds       │
│  Grafana (:3000)        ← Dashboards you can see in your browser │
│  Structured Logs        ← JSON logs with request IDs for search  │
│  Health Checks          ← /health (alive?) and /ready (working?) │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    Redis (:6379)                                  │
│                                                                  │
│  Shared state that multiple components need:                     │
│  - API key storage and lookup                                    │
│  - Rate limiter token buckets (atomic operations)                │
│  - Request queue (sorted sets with priorities)                   │
│  - Usage counters (per-key daily token totals)                   │
│  - Circuit breaker state                                         │
└──────────────────────────────────────────────────────────────────┘
```

## Why This Architecture?

Every layer exists to solve a specific problem:

| Layer | Problem It Solves |
|-------|-------------------|
| nginx | Terminate SSL, buffer slow clients, basic DDoS protection |
| API Gateway (FastAPI) | Route requests, enforce policies, track usage |
| Auth Middleware | Only authorized users can access the GPU |
| Rate Limiter | One user can't hog all the GPU time |
| Request Queue | Handle bursts without dropping requests |
| Inference Service | Abstract away the model server details |
| Safety Filter | Prevent harmful inputs/outputs |
| Circuit Breaker | Don't pile up requests when the GPU is down |
| vLLM | Efficient GPU utilization with batching |
| Observability | Know what's happening without guessing |

## Technology Choices

| Component | Choice | Why This One |
|-----------|--------|-------------|
| API Framework | FastAPI | Async-native, auto-generates OpenAPI docs, great for streaming |
| Model Server | vLLM | Industry standard, continuous batching, OpenAI-compatible API built-in |
| Cache/Queue | Redis | Atomic operations for rate limiting, fast pub/sub, sorted sets for queues |
| Metrics | Prometheus | Pull-based (simple), PromQL is powerful, Grafana integration |
| Dashboards | Grafana | Industry standard, pre-built dashboard ecosystem |
| Logging | structlog | Structured JSON, easy to search, zero-config pretty printing |
| Reverse Proxy | nginx | Battle-tested, SSL termination, request buffering |
| Orchestration | Docker Compose | One command to start everything |
| Internet | Cloudflare Tunnel | No port forwarding needed, free SSL, DDoS protection |

## Model Choice

**Mistral 7B Instruct v0.3 (4-bit GPTQ quantized)**

| Property | Value | Why It Matters |
|----------|-------|---------------|
| Parameters | 7 billion | Small enough for your GPU, smart enough to be useful |
| VRAM (4-bit) | ~4 GB | Leaves ~18GB for KV cache = more concurrent users |
| Context Length | 32K tokens | Long conversations are possible |
| Instruction-tuned | Yes | Follows chat format, gives helpful answers |
| License | Apache 2.0 | Free for any use |

Alternative: Llama 3.1 8B Instruct (4-bit, ~5GB) - slightly better quality, slightly less headroom.
