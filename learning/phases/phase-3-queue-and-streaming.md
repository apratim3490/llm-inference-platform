# Phase 3: Request Queuing, Batching, Streaming

## Goal

Add a priority request queue and Server-Sent Events streaming. After this phase,
requests are queued by tier priority, and streaming mode shows tokens appearing
one-by-one in real-time.

## What You'll Learn

- Priority queue with Redis sorted sets
- Async background workers with asyncio
- Server-Sent Events (SSE) protocol
- Streaming HTTP responses in FastAPI
- Client disconnect detection
- Concurrency control with asyncio.Semaphore

## Concept Docs to Read First

- [04-request-queuing.md](../concepts/04-request-queuing.md)
- [06-streaming-sse.md](../concepts/06-streaming-sse.md)

## Clean Approach Notes

- **Semaphore first, queue second.** A single RTX 3090 handles ~1 inference at a
  time. Start with `asyncio.Semaphore(1)` for concurrency control (simple), then
  add the Redis priority queue as a learning exercise on top.
- **Streaming uses `async def` generators**, not callback patterns. The generator
  itself checks for client disconnect — no separate monitoring task.
- **`StreamingResponse`** wraps the generator directly. Clean and composable.

## Steps

### Step 1: Concurrency Semaphore
**File**: `src/services/inference.py`

Add `asyncio.Semaphore(1)` to limit concurrent vLLM calls. Simple foundation
before adding the full queue.

### Step 2: Priority Request Queue
**File**: `src/services/queue.py`

Redis sorted set with score = (priority × 1e12) + timestamp. Bounded capacity (100).

### Step 3: Queue Worker / Dispatcher
**File**: `src/services/queue.py` (additional logic)

Background asyncio task: dequeue by priority, dispatch to vLLM.

### Step 4: SSE Streaming
**Files**: `src/utils/sse.py`, `src/services/inference.py`, `src/api/v1/schemas/streaming.py`

Clean pattern — async generator with disconnect detection built in:
```python
async def stream_completion(request, client, payload):
    async with client.stream("POST", url, json=payload) as response:
        async for line in response.aiter_lines():
            if await request.is_disconnected():
                break
            yield format_sse(line)
    yield "data: [DONE]\n\n"
```

### Step 5: Update Chat Endpoint
**File**: `src/api/v1/chat.py`

Branch on `stream: true` → `StreamingResponse(generator)` vs JSON response.

### Step 6: Model Upgrade & KV Cache Tuning
**Files**: `src/config.py`, `docker-compose.yml`

Phase 1 uses Mistral 7B (~14GB VRAM) as a safe default. Now that streaming and
concurrency are in place, upgrade the model and tune memory tradeoffs — this is
a real engineering decision that frontier labs face constantly.

**Sub-steps:**

1. **Benchmark 7B baseline** — measure concurrent request capacity, tokens/sec,
   and VRAM usage with `nvidia-smi` while under load.

2. **Upgrade to 14B quantized** (e.g. `Qwen/Qwen2.5-14B-Instruct-AWQ`, ~15GB).
   Update `vllm_model_name` in config and `--model` in Docker Compose.

3. **Tune `--max-model-len`** — shorter context = smaller KV cache = more
   concurrent requests. Try 2048 vs 4096 vs 8192 and measure the tradeoff.

4. **Tune `--gpu-memory-utilization`** — vLLM flag (default 0.9). Lower it to
   leave headroom, raise it to squeeze more KV cache. Find the sweet spot.

5. **Re-benchmark** — compare concurrent capacity and tokens/sec against the 7B
   baseline. Document findings.

**The core tradeoff:**
- Bigger model = better quality, more VRAM for weights, less room for KV cache
- KV cache size = how many concurrent requests fit in memory
- Quantization (AWQ/GPTQ) = smaller weights, freeing VRAM for KV cache
- `--max-model-len` = cap on context length, directly controls KV cache size per request

**VRAM budget (24GB):**
```
| Model weights | + KV cache per request × concurrent requests | ≤ 24GB |
```

### Step 7: Tests

Test queue priority ordering, SSE event format, streaming end-to-end.
Include a concurrency stress test to validate the model/KV cache tuning.

## Verification

```bash
# Streaming test (tokens appear one by one)
curl -N -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-test-pro" \
  -H "Content-Type: application/json" \
  -d '{"model":"mistral-7b","messages":[{"role":"user","content":"Count to 10"}],"stream":true}'

# Priority test: send free-tier request, then admin-tier request
# Admin request should complete first even though it arrived second
```

## Files Created This Phase

```
src/
├── services/
│   └── queue.py         ← Priority queue + worker
├── utils/
│   └── sse.py           ← SSE formatting helpers
└── api/v1/schemas/
    └── streaming.py     ← SSE chunk Pydantic models
```
