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

## Steps

### Step 1: Priority Request Queue
**File**: `src/services/queue.py`

Redis sorted set with score = (priority × 1e12) + timestamp. Bounded capacity (100).

### Step 2: Queue Worker / Dispatcher
**File**: `src/services/queue.py` (additional logic)

Background asyncio task: dequeue by priority, dispatch to vLLM, semaphore for concurrency.

### Step 3: SSE Streaming
**Files**: `src/utils/sse.py`, `src/services/inference.py`, `src/api/v1/schemas/streaming.py`

Proxy vLLM's streaming output as SSE events in OpenAI format.

### Step 4: Client Disconnect Detection
**File**: `src/utils/sse.py`

Check `request.is_disconnected()` during streaming to stop wasting GPU.

### Step 5: Update Chat Endpoint
**File**: `src/api/v1/chat.py`

Branch on `stream: true` → StreamingResponse vs full JSON response.

### Step 6: Tests

Test queue priority ordering, SSE event format, streaming end-to-end.

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
