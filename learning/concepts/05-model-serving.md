# Concept: Model Serving (vLLM)

## What Is It?

Model serving is the layer that actually runs the LLM on your GPU. vLLM is an
open-source inference engine that takes text in, runs it through the neural
network, and produces text out - but it does it in a highly optimized way.

## Why Not Just Load the Model in PyTorch?

Naive PyTorch inference:
- Processes ONE request at a time
- Wastes GPU memory on fragmented KV cache
- No streaming support
- ~5 tokens/second for a 7B model

vLLM inference:
- Processes 8-16 requests SIMULTANEOUSLY (continuous batching)
- Efficient GPU memory with PagedAttention
- Built-in streaming
- ~200+ tokens/second total throughput

That's a 40x improvement. This is why model serving frameworks exist.

## Key Innovations

### 1. Continuous Batching

Traditional batching: Wait for N requests, process them together, return all results.
Problem: Users wait for the batch to fill up.

```
Traditional:  [req1]---wait---[req1,req2,req3]---PROCESS---[results]
              Long wait      ↑ batch formed     Long processing

Continuous:   [req1]---PROCESS
              [req2]--JOIN BATCH--PROCESS
              [req3]----JOIN BATCH--PROCESS
              Requests join the ongoing batch immediately
```

Continuous batching: New requests join the current GPU computation mid-flight.
No waiting. The GPU always has work to do.

### 2. PagedAttention

LLMs need a "KV cache" - memory that stores the conversation context so the
model doesn't reprocess everything for each new token. This cache can be huge.

**Problem**: Traditional allocation reserves a contiguous block per request.
If requests have different lengths, memory fragments and wastes space.

**PagedAttention solution**: Manage GPU memory in small pages (like an OS manages RAM).

```
Traditional (wasteful):
GPU Memory: [req1████████░░░░][req2████░░░░░░░░][req3██░░░░░░░░░░]
                         ↑ wasted       ↑ wasted          ↑ wasted

PagedAttention (efficient):
GPU Memory: [r1][r2][r3][r1][r2][r1][r3][r1][free][free][free]
            Pages allocated on demand, no waste
```

Result: 2-4x more concurrent requests on the same GPU.

### 3. Quantization (4-bit GPTQ)

Your model has 7 billion parameters. At full precision (FP16), each is 2 bytes = 14GB.
At 4-bit quantization, each is 0.5 bytes = ~3.5-4GB.

```
FP16 (full precision):  14GB weights + 10GB KV cache = 24GB → barely fits
4-bit (quantized):       4GB weights + 18GB KV cache = 22GB → room to breathe
```

Quality loss from 4-bit quantization: ~2-5% on benchmarks. Throughput gain: 3-4x
more concurrent users. This tradeoff is a no-brainer for serving.

## vLLM's OpenAI-Compatible API

vLLM exposes an API identical to OpenAI's. This means your FastAPI gateway
doesn't need special client code - it just proxies HTTP requests.

```bash
# Direct to vLLM (port 8001)
curl http://localhost:8001/v1/chat/completions \
  -d '{"model":"mistral","messages":[{"role":"user","content":"Hi"}]}'

# Through your gateway (port 8000) - same format!
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-abc123" \
  -d '{"model":"mistral","messages":[{"role":"user","content":"Hi"}]}'
```

The only difference: your gateway adds auth, rate limiting, safety, observability.

## Your GPU Budget

```
RTX 3090: 24GB VRAM

Model weights (4-bit Mistral 7B):  ~4 GB
vLLM overhead:                     ~1 GB
KV cache (your "concurrent budget"): ~18 GB

Each concurrent request with 2K context ≈ 1-2 GB KV cache
→ You can serve 8-16 concurrent requests

If you reduce max context to 1K: ~16-32 concurrent requests
If you use a larger model (14B): ~4-8 concurrent requests
```

## Files You'll Build

| File | Purpose |
|------|---------|
| `docker-compose.yml` (vLLM service) | Container config for vLLM |
| `src/services/inference.py` | HTTP client that proxies to vLLM |
| `src/config.py` (vLLM settings) | vLLM URL, model name, timeout config |
