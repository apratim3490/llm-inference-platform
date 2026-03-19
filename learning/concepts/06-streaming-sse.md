# Concept: Streaming with Server-Sent Events (SSE)

## What Is It?

Instead of waiting for the entire response to generate (which can take seconds),
streaming sends each token to the client immediately as it's generated. The user
sees text appear word-by-word in real-time.

## Why Does It Exist?

Without streaming:
- User sends "Write me a poem" → waits 5-10 seconds → gets full response
- Bad UX: feels slow and unresponsive
- If the response is wrong, user wasted 10 seconds waiting

With streaming:
- User sends "Write me a poem" → sees first word in ~200ms → text flows in
- Great UX: feels fast and interactive
- User can cancel early if the response is going in the wrong direction

## Real-World Analogy

**Without streaming**: Ordering food at a restaurant where the waiter brings
everything at once. You wait 45 minutes, then everything arrives.

**With streaming**: A sushi conveyor belt. Each piece arrives as it's made.
You start eating immediately. If you don't like what you see, you stop ordering.

## How SSE Works

Server-Sent Events is a simple protocol built on HTTP:

```
Client                                    Server
  │                                          │
  │  POST /v1/chat/completions               │
  │  stream: true                            │
  │─────────────────────────────────────────>│
  │                                          │
  │  HTTP 200 OK                             │
  │  Content-Type: text/event-stream         │
  │<─────────────────────────────────────────│
  │                                          │
  │  data: {"choices":[{"delta":{"content":"TCP"}}]}
  │<─────────────────────────────────────────│
  │                                          │
  │  data: {"choices":[{"delta":{"content":" is"}}]}
  │<─────────────────────────────────────────│
  │                                          │
  │  data: {"choices":[{"delta":{"content":" a"}}]}
  │<─────────────────────────────────────────│
  │                                          │
  │  data: [DONE]                            │
  │<─────────────────────────────────────────│
  │                                          │
  │  (connection closes)                     │
```

### The Format

Each SSE event is:
```
data: {JSON payload}\n\n
```

That's it. `data:` prefix, JSON, two newlines. The two newlines mark the end
of one event. The client reads line by line and parses each event.

### Streaming vs Non-Streaming Response

**Non-streaming** (stream: false):
```json
{
  "choices": [{
    "message": {"role": "assistant", "content": "TCP is a protocol..."},
    "finish_reason": "stop"
  }],
  "usage": {"prompt_tokens": 7, "completion_tokens": 23, "total_tokens": 30}
}
```

**Streaming** (stream: true) - each chunk:
```json
{"choices": [{"delta": {"content": "TCP"}, "finish_reason": null}]}
{"choices": [{"delta": {"content": " is"}, "finish_reason": null}]}
{"choices": [{"delta": {"content": " a"}, "finish_reason": null}]}
{"choices": [{"delta": {"content": " protocol"}, "finish_reason": null}]}
{"choices": [{"delta": {}, "finish_reason": "stop"}]}
```

Key differences:
- `message` → `delta` (it's a diff, not the full message)
- Each chunk has only the NEW content
- Final chunk has `finish_reason: "stop"` and empty delta
- Usage stats come in the final chunk (or a separate event)

## Client Disconnect Detection

Critical optimization: If the user closes their browser tab, STOP generating.

```python
async def stream_response(request: Request):
    async for token in vllm_stream:
        if await request.is_disconnected():
            # Client left! Stop wasting GPU cycles
            logger.info("Client disconnected, aborting generation")
            break
        yield f"data: {token_to_json(token)}\n\n"
```

At frontier labs, this saves millions of dollars in GPU time. On your RTX 3090,
it frees the GPU for the next request faster.

## Time to First Token (TTFT)

TTFT is the most important metric for streaming UX:

```
Request sent ─────── TTFT ──────── First token appears
                     200ms              ↓
                                    "TCP" ... "is" ... "a" ...
```

TTFT depends on:
- Queue wait time (Phase 3)
- Input processing time (tokenization, safety check)
- GPU "prefill" time (processing the input prompt)

After the first token, each subsequent token arrives every ~30-50ms (called
"inter-token latency" or "time per output token").

## Files You'll Build

| File | Purpose |
|------|---------|
| `src/utils/sse.py` | SSE formatting helpers |
| `src/services/inference.py` (streaming mode) | Proxy vLLM's streaming response |
| `src/api/v1/chat.py` (streaming branch) | Return StreamingResponse when stream=true |
| `src/api/v1/schemas/streaming.py` | SSE chunk Pydantic models |
