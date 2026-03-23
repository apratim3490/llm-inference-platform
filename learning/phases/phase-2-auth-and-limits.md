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
- **Router-level dependencies for auth** — apply `Depends(enforce_rate_limit)` at
  the router level in `router.py` so individual endpoints don't repeat it:
  ```python
  api_router.include_router(chat_router, prefix="/v1", dependencies=[Depends(enforce_rate_limit)])
  ```
  `/health` stays outside this router, so it never requires auth.
- **`keys.yaml` must be gitignored** — even dev keys shouldn't be in source
  control if they contain raw secrets. The seed script generates and prints keys
  once; only hashes are stored in Redis.
- **Skeleton files `src/middleware/auth.py` and `src/middleware/rate_limiter.py`
  should NOT be used** — auth lives in `src/dependencies.py`, rate limiting in
  `src/services/rate_limiter.py`. Delete or repurpose those middleware skeletons.

## Steps

### Step 1: Add Redis to Podman Compose + Lifespan

**Files**: `docker-compose.yml`, `src/main.py`, `src/dependencies.py`

Add Redis 7 service to Compose. Add `redis.asyncio.Redis` to lifespan →
`app.state.redis`. Create `get_redis()` dependency in `src/dependencies.py`.

### Step 2: Tier Enum + API Key Data Model

**Files**: `src/models/enums.py`, `src/models/api_key.py`

Define Tier enum (free/pro/admin) and APIKey frozen dataclass with tier-based
rate limit defaults (RPM + TPM).

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

Applied at router level — endpoints don't need to declare auth individually.

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

### Step 5: Request ID Middleware

**File**: `src/middleware/request_id.py`

UUID per request, X-Request-ID header, attached to all logs.
This IS appropriate as middleware — it genuinely runs on every request.

### Step 6: Token Counter

**File**: `src/utils/token_counter.py`

Use tiktoken to count input tokens pre-inference (feeds TPM limiter and usage
tracker).

### Step 7: Usage Tracker

**File**: `src/services/usage_tracker.py`

Record per-request usage, maintain daily totals in Redis hashes.

### Step 8: Key Generation + Seed Scripts

**Files**: `scripts/generate_api_key.py`, `scripts/seed_redis.py`

CLI tool to create new API keys (prints raw key once, stores hash in Redis).
Seed script loads dev/test keys for local development.

### Step 9: Tests

Test auth rejection (401), rate limit enforcement (429), token counting
accuracy, usage tracking, request ID propagation.

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

# Request ID header present
curl -v http://localhost:8000/health 2>&1 | grep x-request-id
# → x-request-id: 550e8400-e29b-41d4-a716-446655440000
```

## Files Created This Phase

```
src/
├── dependencies.py      ← Auth + rate limit + Redis dependencies (updated)
├── middleware/
│   ├── __init__.py
│   └── request_id.py    ← UUID per request (only true middleware)
├── services/
│   ├── rate_limiter.py  ← Token bucket with Redis Lua script
│   └── usage_tracker.py ← Per-key token counting
├── models/
│   ├── __init__.py
│   ├── api_key.py       ← APIKey frozen dataclass
│   ├── usage.py         ← UsageRecord dataclass
│   └── enums.py         ← Tier enum
└── utils/
    ├── __init__.py
    └── token_counter.py ← tiktoken wrapper

scripts/
├── generate_api_key.py  ← CLI key generator
└── seed_redis.py        ← Load dev keys
```
