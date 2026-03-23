# Phase 2 Progress: Authentication, Rate Limiting, Usage Tracking

## Status: IN PROGRESS
## Started: 2026-03-23
## Approach: Self-implementation with Claude guidance

## Steps

| # | Step | Status | File(s) |
|---|------|--------|---------|
| 1 | Redis to Podman Compose + lifespan | DONE | `docker-compose.yml`, `src/main.py`, `src/dependencies.py`, `src/config.py` |
| 2 | Tier enum + API Key dataclass | DONE | `src/models/enums.py`, `src/models/api_key.py` |
| 3 | Authentication dependency | DONE | `src/dependencies.py` |
| 4 | Token bucket rate limiter | IN PROGRESS | `src/services/rate_limiter.py` |
| 5 | Request ID middleware | TODO | `src/middleware/request_id.py` |
| 6 | Token counter (tiktoken) | TODO | `src/utils/token_counter.py` |
| 7 | Usage tracker | TODO | `src/services/usage_tracker.py` |
| 8 | Key gen + seed scripts | TODO | `scripts/generate_api_key.py`, `scripts/seed_redis.py` |
| 9 | Tests | TODO | `tests/` |

## Recommended Build Order

1. Redis + lifespan (DONE) → 2. enums + APIKey (DONE) → 3. auth dependency (DONE)
→ 4. rate limiter (IN PROGRESS) → 5. request ID → 6. token counter → 7. usage tracker
→ 8. key gen scripts → 9. tests

## Clean Patterns (applied)

- **`Depends()` for auth and rate limiting** — NOT middleware
- **Router-level dependencies** — `enforce_rate_limit` applied at router level
- **Dependency chaining** — `enforce_rate_limit` → `require_auth` → `get_redis`
- **Redis Lua scripts** for atomic rate limit operations
- **`cast()` for `app.state`** — typed access to untyped state

## File Cleanup Done

- Deleted `src/middleware/auth.py` (auth moved to `dependencies.py`)
- Moved `src/middleware/rate_limiter.py` → `src/services/rate_limiter.py`
- Created `scripts/generate_api_key.py`, `scripts/seed_redis.py` skeletons
