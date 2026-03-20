# Phase 2: Authentication, Rate Limiting, Usage Tracking

## Goal

Protect the API with API keys, enforce per-key rate limits (RPM + TPM), and
track token usage per key. After this phase, unauthorized requests get 401,
over-limit requests get 429, and every request's token usage is recorded.

## What You'll Learn

- API key authentication pattern (hash-then-lookup)
- Token bucket rate limiting algorithm
- Redis Lua scripts for atomic operations
- Token counting with tiktoken
- Per-key usage accumulation
- FastAPI `Depends()` for auth and rate limiting (NOT middleware)

## Concept Docs to Read First

- [02-authentication.md](../concepts/02-authentication.md)
- [03-rate-limiting.md](../concepts/03-rate-limiting.md)
- [07-usage-tracking.md](../concepts/07-usage-tracking.md)

## Clean Approach Notes

- **Auth and rate limiting use `Depends()`, NOT middleware.** Dependencies only run
  on routes that declare them — no fragile skip-lists for `/health`, `/docs`, etc.
  `RequestIDMiddleware` is the exception: it genuinely runs on every request.
- **Redis connection pool in lifespan**, not per-request connections. Add to
  `app.state.redis` alongside the httpx client.
- **Token bucket MUST use a Redis Lua script** for atomicity. Never do
  check-then-decrement in two separate calls — that's a race condition.
- **Auth dependency chains into rate limiter** — `require_auth` returns `APIKey`,
  `enforce_rate_limit` depends on `require_auth` so it gets the key automatically.

## Steps

### Step 1: Add Redis to Docker Compose + Lifespan

Add Redis 7 service. Add `redis.asyncio.Redis` to lifespan → `app.state.redis`.
Create `get_redis()` dependency in `src/dependencies.py`.

### Step 2: API Key Data Model

**Files**: `src/models/api_key.py`, `src/models/enums.py`, `config/api_keys/keys.yaml`

Define the APIKey frozen dataclass with tier system (free/pro/admin).

### Step 3: Authentication as Dependency

**File**: `src/dependencies.py`

Clean pattern — a dependency function, not middleware:
```python
async def require_auth(
    request: Request,
    redis: Redis = Depends(get_redis),
) -> APIKey:
    # Extract Bearer token, SHA-256 hash, Redis lookup
    # Raise HTTPException(401) if invalid
    # Return APIKey on success
```

Endpoints declare: `api_key: APIKey = Depends(require_auth)`

### Step 4: Token Bucket Rate Limiter as Dependency

**File**: `src/services/rate_limiter.py`

Clean pattern — chains from auth dependency:
```python
async def enforce_rate_limit(
    api_key: APIKey = Depends(require_auth),
    redis: Redis = Depends(get_redis),
) -> APIKey:
    # Redis Lua script for atomic check-and-decrement (RPM + TPM)
    # Raise HTTPException(429) with Retry-After header if exceeded
    # Return api_key (pass-through for chaining)
```

### Step 5: Token Counter

**File**: `src/utils/token_counter.py`

Use tiktoken to count input tokens pre-inference (feeds TPM limiter and usage tracker).

### Step 6: Usage Tracker

**File**: `src/services/usage_tracker.py`

Record per-request usage, maintain daily totals in Redis hashes.

### Step 7: Request ID Middleware

**File**: `src/middleware/request_id.py`

UUID per request, X-Request-ID header, attached to all logs.
This IS appropriate as middleware — it genuinely runs on every request.

### Step 8: Key Generation Script

**File**: `scripts/generate_api_key.py`

CLI tool to create and store new API keys.

### Step 9: Tests

Test auth rejection, rate limit enforcement, token counting accuracy.

## Verification

```bash
# No key → 401
curl http://localhost:8000/v1/chat/completions -X POST -d '...'
# → 401 Unauthorized

# Valid key → 200
curl -H "Authorization: Bearer sk-test-admin" http://localhost:8000/v1/chat/completions ...
# → 200 OK with chat completion

# Exceed rate limit → 429
for i in $(seq 1 15); do curl -H "Authorization: Bearer sk-test-free" ...; done
# → 429 Too Many Requests (after 10 requests for free tier)
```

## Files Created This Phase

```
src/
├── dependencies.py      ← Auth + rate limit dependencies (updated)
├── middleware/
│   ├── __init__.py
│   └── request_id.py    ← UUID per request (only true middleware)
├── services/
│   └── usage_tracker.py ← Per-key token counting
├── models/
│   ├── __init__.py
│   ├── api_key.py       ← APIKey dataclass
│   ├── usage.py         ← UsageRecord dataclass
│   └── enums.py         ← Tier, Priority enums
└── utils/
    ├── __init__.py
    └── token_counter.py ← tiktoken wrapper

scripts/
├── generate_api_key.py  ← CLI key generator
└── seed_redis.py        ← Load dev keys
```
