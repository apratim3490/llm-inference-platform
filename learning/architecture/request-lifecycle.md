# The Life of a Request

Follow a single API request from the moment it leaves your terminal to the moment
tokens appear on your screen. Every numbered step maps to a real component you'll build.

## The Request

```bash
curl -X POST https://your-api.example.com/v1/chat/completions \
  -H "Authorization: Bearer sk-abc123" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral-7b",
    "messages": [{"role": "user", "content": "Explain TCP in one sentence"}],
    "stream": true,
    "max_tokens": 100
  }'
```

## Step-by-Step Journey

```
 ┌─────────────────────────────────────────────────────────────┐
 │  STEP 1: DNS + TLS                                          │
 │                                                              │
 │  Your curl → Cloudflare DNS → Cloudflare Tunnel → nginx     │
 │                                                              │
 │  What happens:                                               │
 │  - DNS resolves your-api.example.com to Cloudflare's edge   │
 │  - TLS handshake encrypts the connection                    │
 │  - Cloudflare Tunnel forwards to your home nginx            │
 │  - nginx terminates SSL, forwards HTTP to FastAPI :8000     │
 │                                                              │
 │  Latency added: ~20-50ms (internet + tunnel overhead)       │
 └──────────────────────────┬──────────────────────────────────┘
                            ▼
 ┌─────────────────────────────────────────────────────────────┐
 │  STEP 2: Request ID Assignment                               │
 │  File: src/middleware/request_id.py                          │
 │                                                              │
 │  req_id = "req_a1b2c3d4-e5f6-7890-abcd-ef1234567890"       │
 │                                                              │
 │  Every single request gets a unique UUID. This ID follows   │
 │  the request through EVERY log line, metric, and error.     │
 │  When something goes wrong at 3am, this ID is how you       │
 │  trace exactly what happened.                                │
 │                                                              │
 │  Think of it like: A tracking number for a package.          │
 │  Latency added: <0.01ms                                     │
 └──────────────────────────┬──────────────────────────────────┘
                            ▼
 ┌─────────────────────────────────────────────────────────────┐
 │  STEP 3: Authentication                                      │
 │  File: src/middleware/auth.py                                │
 │                                                              │
 │  Header: "Authorization: Bearer sk-abc123"                  │
 │                                                              │
 │  1. Extract "sk-abc123" from the header                     │
 │  2. Hash it: SHA-256("sk-abc123") → "7f3a..."              │
 │  3. Look up "7f3a..." in Redis                              │
 │  4. Found? → Attach key metadata (tier=pro, name="Alice")  │
 │     Not found? → Return 401 Unauthorized, STOP HERE         │
 │                                                              │
 │  Why hash? You never store raw API keys. If Redis is        │
 │  breached, attackers get useless hashes, not working keys.  │
 │                                                              │
 │  Think of it like: A bouncer checking your ID at the door.  │
 │  Latency added: ~1ms (Redis lookup)                         │
 └──────────────────────────┬──────────────────────────────────┘
                            ▼
 ┌─────────────────────────────────────────────────────────────┐
 │  STEP 4: Rate Limiting                                       │
 │  File: src/middleware/rate_limiter.py                        │
 │                                                              │
 │  Two checks for API key "sk-abc123" (pro tier):             │
 │                                                              │
 │  RPM check: 58/60 requests this minute → PASS (2 left)     │
 │  TPM check: 45000/100000 tokens this minute → PASS          │
 │                                                              │
 │  Algorithm: Token Bucket                                     │
 │  - Bucket starts full (60 tokens for RPM)                   │
 │  - Each request removes 1 token                             │
 │  - Tokens refill at a steady rate (1 per second for RPM)    │
 │  - If bucket is empty → 429 Too Many Requests + Retry-After │
 │                                                              │
 │  Why Redis? The Lua script that checks-and-decrements is    │
 │  ATOMIC - even with 100 concurrent requests, no race conds. │
 │                                                              │
 │  Think of it like: A turnstile that only lets N people      │
 │  through per minute.                                         │
 │  Latency added: ~1ms (Redis Lua script)                     │
 └──────────────────────────┬──────────────────────────────────┘
                            ▼
 ┌─────────────────────────────────────────────────────────────┐
 │  STEP 5: Request Validation                                  │
 │  File: src/api/v1/schemas/chat.py (Pydantic models)        │
 │                                                              │
 │  Pydantic validates the JSON body:                          │
 │  ✓ "model" is a string                                      │
 │  ✓ "messages" is a non-empty list                           │
 │  ✓ Each message has "role" (user/assistant/system)          │
 │  ✓ Each message has "content" (string)                      │
 │  ✓ "max_tokens" is a positive integer ≤ 4096               │
 │  ✓ "stream" is a boolean                                    │
 │                                                              │
 │  Invalid? → Return 400 Bad Request with details, STOP HERE  │
 │                                                              │
 │  Think of it like: A form checker that rejects incomplete   │
 │  applications before they reach the reviewer.                │
 │  Latency added: <0.1ms                                      │
 └──────────────────────────┬──────────────────────────────────┘
                            ▼
 ┌─────────────────────────────────────────────────────────────┐
 │  STEP 6: Input Safety Filter                                 │
 │  File: src/services/safety.py                               │
 │                                                              │
 │  Scan user message: "Explain TCP in one sentence"           │
 │                                                              │
 │  ✓ No blocked keywords found                                │
 │  ✓ No PII patterns (SSN, credit card) detected              │
 │  ✓ No prompt injection patterns detected                    │
 │  → Result: SAFE, proceed                                    │
 │                                                              │
 │  If UNSAFE → Return 400 with content_filter error, STOP     │
 │                                                              │
 │  Think of it like: Airport security scanning your bag.       │
 │  Latency added: <1ms (regex/keyword), ~10ms (if classifier) │
 └──────────────────────────┬──────────────────────────────────┘
                            ▼
 ┌─────────────────────────────────────────────────────────────┐
 │  STEP 7: Token Counting (Pre-inference)                      │
 │  File: src/utils/token_counter.py                           │
 │                                                              │
 │  Count input tokens using tiktoken (same tokenizer as the   │
 │  model): "Explain TCP in one sentence" → 7 tokens           │
 │                                                              │
 │  This count is used for:                                     │
 │  - TPM rate limiting (counted against token budget)          │
 │  - Usage tracking (input_tokens field in billing)            │
 │  - Logging (so you know the request size)                    │
 │                                                              │
 │  Think of it like: Weighing a package before shipping it.    │
 │  Latency added: <0.1ms                                      │
 └──────────────────────────┬──────────────────────────────────┘
                            ▼
 ┌─────────────────────────────────────────────────────────────┐
 │  STEP 8: Request Queue                                       │
 │  File: src/services/queue.py                                │
 │                                                              │
 │  API key tier = "pro" → Priority 1                          │
 │  Queue score = (1 × 1,000,000,000,000) + timestamp          │
 │                                                              │
 │  Current queue:                                              │
 │  ┌────────────────────────────────────────────┐             │
 │  │ P0: [admin-req-001]                        │  ← first    │
 │  │ P1: [pro-req-042] [pro-req-043] [YOUR REQ] │  ← second   │
 │  │ P2: [free-req-100] [free-req-101]          │  ← last     │
 │  └────────────────────────────────────────────┘             │
 │                                                              │
 │  Your request waits until pro-req-042 and 043 are done.     │
 │  But it goes before ALL free-tier requests, even earlier.   │
 │                                                              │
 │  Think of it like: Airport boarding - first class, business, │
 │  then economy. Within each class, it's first-come.          │
 │  Latency added: 0ms to seconds (depends on queue depth)     │
 └──────────────────────────┬──────────────────────────────────┘
                            ▼
 ┌─────────────────────────────────────────────────────────────┐
 │  STEP 9: Circuit Breaker Check                               │
 │  File: src/services/circuit_breaker.py                      │
 │                                                              │
 │  Current state: CLOSED (normal operation)                   │
 │                                                              │
 │  States:                                                     │
 │  CLOSED    → Everything fine, forward request to vLLM       │
 │  OPEN      → vLLM is down, immediately return 503           │
 │  HALF_OPEN → Try one request to see if vLLM recovered       │
 │                                                              │
 │  If vLLM has failed 5 times in a row → switch to OPEN      │
 │  After 30 seconds of OPEN → switch to HALF_OPEN             │
 │  If HALF_OPEN request succeeds → switch to CLOSED           │
 │                                                              │
 │  Think of it like: A fuse in your electrical panel. When    │
 │  too much current flows (too many errors), the fuse trips   │
 │  to protect the system. You reset it manually (or wait).    │
 │  Latency added: <0.01ms (just a state check)                │
 └──────────────────────────┬──────────────────────────────────┘
                            ▼
 ┌─────────────────────────────────────────────────────────────┐
 │  STEP 10: Inference (The Main Event!)                        │
 │  File: src/services/inference.py → vLLM (:8001)            │
 │                                                              │
 │  FastAPI sends HTTP POST to vLLM's /v1/chat/completions     │
 │  with stream=true.                                           │
 │                                                              │
 │  Inside vLLM:                                                │
 │  1. Tokenize input: "Explain TCP..." → [token IDs]         │
 │  2. Add to continuous batch (maybe alongside other reqs)    │
 │  3. Run forward pass on GPU                                  │
 │  4. Sample next token                                        │
 │  5. Stream it back immediately                               │
 │  6. Repeat 4-5 until done or max_tokens reached             │
 │                                                              │
 │  Key vLLM innovations:                                       │
 │  - Continuous batching: new requests join mid-generation    │
 │  - PagedAttention: GPU memory managed like OS virtual memory│
 │  - These let you serve 8-16 concurrent users on one GPU     │
 │                                                              │
 │  Think of it like: A chef who can cook multiple dishes at   │
 │  once, adding new orders to the stove without stopping.     │
 │  Latency: 200ms-2s for first token, then ~30ms per token   │
 └──────────────────────────┬──────────────────────────────────┘
                            ▼
 ┌─────────────────────────────────────────────────────────────┐
 │  STEP 11: Streaming Response (SSE)                           │
 │  File: src/utils/sse.py                                     │
 │                                                              │
 │  As each token arrives from vLLM, FastAPI wraps it in an    │
 │  SSE (Server-Sent Events) format and sends it immediately:  │
 │                                                              │
 │  data: {"choices":[{"delta":{"content":"TCP"}}]}            │
 │                                                              │
 │  data: {"choices":[{"delta":{"content":" is"}}]}            │
 │                                                              │
 │  data: {"choices":[{"delta":{"content":" a"}}]}             │
 │                                                              │
 │  data: {"choices":[{"delta":{"content":" protocol"}}]}      │
 │                                                              │
 │  data: [DONE]                                                │
 │                                                              │
 │  The client sees tokens appear one by one in real-time.     │
 │  If the client disconnects, we STOP generating (don't waste │
 │  GPU cycles on tokens nobody will read).                     │
 │                                                              │
 │  Think of it like: A live sports ticker - scores appear as  │
 │  they happen, you don't wait for the whole game to end.     │
 └──────────────────────────┬──────────────────────────────────┘
                            ▼
 ┌─────────────────────────────────────────────────────────────┐
 │  STEP 12: Output Safety Filter                               │
 │  File: src/services/safety.py                               │
 │                                                              │
 │  Each generated chunk is scanned before being sent to the   │
 │  client. Buffer a few tokens to check for multi-word        │
 │  patterns before releasing them.                             │
 │                                                              │
 │  Generated: "TCP is a protocol..." → SAFE, send it          │
 │                                                              │
 │  If unsafe content detected mid-stream:                     │
 │  → Stop generation, send SSE error event, log incident      │
 └──────────────────────────┬──────────────────────────────────┘
                            ▼
 ┌─────────────────────────────────────────────────────────────┐
 │  STEP 13: Usage Tracking                                     │
 │  File: src/services/usage_tracker.py                        │
 │                                                              │
 │  Request complete! Record usage in Redis:                    │
 │                                                              │
 │  {                                                           │
 │    "request_id": "req_a1b2c3d4...",                         │
 │    "api_key": "sk-abc123" (hashed),                         │
 │    "model": "mistral-7b",                                   │
 │    "input_tokens": 7,                                        │
 │    "output_tokens": 23,                                      │
 │    "total_tokens": 30,                                       │
 │    "latency_ms": 890,                                        │
 │    "time_to_first_token_ms": 210,                            │
 │    "timestamp": "2026-03-18T14:30:00Z"                      │
 │  }                                                           │
 │                                                              │
 │  Daily counter for sk-abc123: 45030 → 45060 total tokens    │
 │                                                              │
 │  This is the data that billing systems use to charge users. │
 │  Think of it like: Your electric meter tracking kWh usage.   │
 └──────────────────────────┬──────────────────────────────────┘
                            ▼
 ┌─────────────────────────────────────────────────────────────┐
 │  STEP 14: Metrics + Logging                                  │
 │  Files: src/observability/metrics.py, logging_config.py     │
 │                                                              │
 │  Prometheus metrics updated:                                 │
 │  - request_duration_seconds: 0.89s (histogram)              │
 │  - time_to_first_token_seconds: 0.21s (histogram)           │
 │  - tokens_processed_total: +30 (counter)                    │
 │  - requests_total: +1 with labels {status=200, tier=pro}    │
 │                                                              │
 │  Structured log line emitted:                                │
 │  {                                                           │
 │    "request_id": "req_a1b2c3d4...",                         │
 │    "method": "POST",                                         │
 │    "path": "/v1/chat/completions",                           │
 │    "status": 200,                                            │
 │    "latency_ms": 890,                                        │
 │    "input_tokens": 7,                                        │
 │    "output_tokens": 23,                                      │
 │    "api_key_tier": "pro",                                    │
 │    "model": "mistral-7b"                                     │
 │  }                                                           │
 │                                                              │
 │  Grafana dashboards update in real-time.                     │
 └─────────────────────────────────────────────────────────────┘
```

## Total Latency Breakdown

| Step | Latency | Notes |
|------|---------|-------|
| DNS + TLS + Tunnel | 20-50ms | One-time per connection |
| Request ID | <0.01ms | UUID generation |
| Auth (Redis lookup) | ~1ms | Single Redis GET |
| Rate Limiter (Redis Lua) | ~1ms | Atomic Lua script |
| Validation (Pydantic) | <0.1ms | CPU-only |
| Safety Filter (keyword) | <1ms | Regex matching |
| Token Counting | <0.1ms | tiktoken, CPU-only |
| Queue Wait | 0ms - seconds | Depends on load |
| Circuit Breaker Check | <0.01ms | In-memory state |
| **Inference (GPU)** | **200ms - 30s** | **This dominates everything** |
| SSE Streaming | ~0ms per chunk | Immediate forwarding |
| Usage Tracking | ~1ms | Redis INCR |
| Metrics + Logging | <1ms | In-process |

**Key insight**: The GPU inference step is 99% of the total latency. Everything else
is overhead we add for security, reliability, and observability - and it's worth it
because it totals <10ms.
