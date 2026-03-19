# Concept: Rate Limiting

## What Is It?

Rate limiting controls how many requests or tokens a user can consume in a given
time window. It protects your GPU from being monopolized by a single user and
ensures fair access for everyone.

## Why Does It Exist?

Without rate limiting:
- One user could send 1000 requests/second and block everyone else
- A bug in a client SDK could accidentally DDoS your GPU
- You can't offer different service levels (free vs paid)
- Your system has no backpressure mechanism

## Real-World Analogy

Think of a water faucet with a flow restrictor:
- Water (requests) can only flow at a certain rate
- If you try to force more through, it backs up
- Different faucets (tiers) have different flow rates
- The restrictor refills automatically over time

## The Algorithm: Token Bucket

This is the industry-standard algorithm used by AWS, Anthropic, and OpenAI.

### How It Works

```
Imagine a bucket that holds 60 tokens (RPM limit = 60):

Time 0:00  Bucket: [████████████████████████████████] 60/60
           Request arrives → take 1 token → ALLOWED

Time 0:01  Bucket: [███████████████████████████████░] 59/60
           Refill: +1 token per second

Time 0:30  Bucket: [██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 5/60
           30 requests used, 25 refilled

Time 0:45  Bucket: [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0/60
           Request arrives → no tokens → 429 REJECTED
           Retry-After: 1 second (when next token arrives)
```

### Two Buckets Per Key

Each API key has TWO rate limit buckets:

1. **RPM (Requests Per Minute)**: How many requests you can make
   - Prevents request flooding
   - Free tier: 10 RPM, Pro: 60 RPM

2. **TPM (Tokens Per Minute)**: How many tokens you can consume
   - Prevents a few large requests from hogging the GPU
   - A single request with max_tokens=4096 uses more "budget" than "Hello"
   - Free tier: 10K TPM, Pro: 100K TPM

### Why Redis + Lua?

The rate limiter must be **atomic**: check the bucket AND decrement it in one
operation. Otherwise, two simultaneous requests could both see "1 token left"
and both proceed (race condition).

Redis Lua scripts execute atomically - the entire script runs without interruption.

```lua
-- Simplified token bucket Lua script
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

-- Get current bucket state
local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1]) or capacity
local last_refill = tonumber(bucket[2]) or now

-- Calculate refill
local elapsed = now - last_refill
local new_tokens = math.min(capacity, tokens + elapsed * refill_rate)

-- Check if enough tokens
if new_tokens >= requested then
    -- Consume tokens
    redis.call('HMSET', key, 'tokens', new_tokens - requested, 'last_refill', now)
    redis.call('EXPIRE', key, 120)
    return 1  -- ALLOWED
else
    return 0  -- REJECTED
end
```

## HTTP Response Headers

When rate-limited, the API returns headers so clients can self-throttle:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 2
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1710769260
```

## What Frontier Labs Do Differently

| Yours | Frontier Lab |
|-------|-------------|
| Single Redis | Redis Cluster for distributed counting |
| 2 limits (RPM, TPM) | Additional: concurrent requests, daily cap, org-level |
| Fixed tiers | Custom limits per customer (enterprise contracts) |
| Simple Lua script | Same Lua approach but with more edge cases handled |

The algorithm is the same. The scale of state management is what differs.

## Files You'll Build

| File | Purpose |
|------|---------|
| `src/middleware/rate_limiter.py` | Token bucket middleware with Redis Lua |
| `src/utils/token_counter.py` | Count tokens before inference (for TPM) |
| `tests/unit/test_rate_limiter.py` | Verify bucket behavior and edge cases |
