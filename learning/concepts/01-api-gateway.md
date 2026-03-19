# Concept: API Gateway

## What Is It?

The API gateway is the front door to your entire system. Every request from every
user passes through it. It's the single entry point that handles authentication,
validation, rate limiting, and routing before any request reaches the expensive
GPU.

## Why Does It Exist?

Without a gateway, every backend service would need to implement its own auth,
rate limiting, logging, and error handling. The gateway centralizes these
"cross-cutting concerns" so the model server can focus on one thing: running
the model.

## Real-World Analogy

Think of a hotel front desk:
- They check your reservation (authentication)
- They enforce occupancy limits (rate limiting)
- They validate your payment (input validation)
- They direct you to the right room (routing)
- They log your check-in (observability)

The hotel rooms (GPU) don't need to do any of this.

## What Frontier Labs Do

| Aspect | Frontier Lab | Your Version |
|--------|-------------|--------------|
| Framework | Custom Go/Rust service | FastAPI (Python) |
| Protocol | HTTP/2 + gRPC internally | HTTP/1.1 with async |
| Instances | Hundreds behind a load balancer | 1 process |
| API Format | OpenAI-compatible or custom | OpenAI-compatible |

## Key Design Decisions

### Why FastAPI?

1. **Async-native**: Built on Starlette, uses Python's asyncio. Perfect for
   I/O-bound work (proxying to vLLM, talking to Redis).
2. **Auto-generated docs**: Visit `/docs` and get interactive API documentation
   for free (Swagger/OpenAPI).
3. **Pydantic integration**: Request/response validation using Python type hints.
4. **Streaming support**: `StreamingResponse` makes SSE trivial.

### Why OpenAI-Compatible Format?

The OpenAI chat completions format (`/v1/chat/completions`) is the de facto
standard. By implementing this format:
- Any OpenAI SDK client works with your API (Python, Node, etc.)
- Tools like LangChain, LlamaIndex connect without modification
- You learn the actual API format used in production

### Middleware Pipeline

Requests flow through middleware in order. Each middleware can:
- **Pass**: Forward the request to the next middleware
- **Reject**: Return an error response immediately (short-circuit)
- **Enrich**: Add data to the request (like request ID, auth info)

```
Request → [Request ID] → [Auth] → [Rate Limit] → [Validation] → [Handler]
                                        ↓ (if over limit)
                                    429 Response
```

## Files You'll Build

| File | Purpose |
|------|---------|
| `src/main.py` | App factory, middleware registration, lifespan |
| `src/config.py` | Environment-based configuration |
| `src/api/router.py` | Route aggregation |
| `src/api/v1/chat.py` | Chat completions endpoint |
| `src/api/v1/models.py` | Model listing endpoint |
| `src/api/v1/health.py` | Health check endpoints |

## Common Interview Questions

- **"Why not just expose vLLM directly?"** - Because you need auth, rate limiting,
  safety filtering, and observability. The model server should only serve the model.
- **"Why middleware pattern vs explicit checks?"** - Middleware keeps each concern
  separate and composable. You can add/remove/reorder without touching endpoint code.
- **"How does this scale?"** - Run multiple FastAPI instances behind a load balancer.
  The gateway is stateless (state is in Redis), so horizontal scaling is trivial.
