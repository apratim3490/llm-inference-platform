# Phase 7: Expose Over Internet

## Goal

Make the API accessible from anywhere via Cloudflare Tunnel. Run load tests
to verify stability. Write comprehensive documentation.

## What You'll Learn

- Cloudflare Tunnel setup and configuration
- Defense in depth (multiple security layers)
- Load testing methodology
- End-to-end testing
- Infrastructure documentation

## Concept Docs to Read First

- [12-internet-exposure.md](../concepts/12-internet-exposure.md)

## Steps

### Step 1: Cloudflare Tunnel
Add `cloudflared` container to Docker Compose. Configure tunnel to proxy to nginx.

### Step 2: Alternative Setup (DynDNS)
Document the port-forwarding approach for those who prefer it.

### Step 3: IP Allowlisting (Optional)
nginx allow/deny directives for extra security.

### Step 4: Load Testing
**File**: `scripts/load_test.py`

Concurrent requests with aiohttp. Measure p50/p95/p99 latency, throughput, errors.

### Step 5: End-to-End Test
**File**: `tests/e2e/test_full_flow.py`

Full flow: generate key → auth request → streaming → check usage → verify metrics.

### Step 6: Documentation
README, architecture docs, API reference, deployment guide.

## Verification

```bash
# From your phone or a different network
curl https://your-api.example.com/v1/chat/completions \
  -H "Authorization: Bearer sk-your-key" \
  -d '{"model":"mistral-7b","messages":[{"role":"user","content":"Hello from the internet!"}],"stream":true}'

# Load test
python scripts/load_test.py --concurrency 10 --duration 60
# → Stable p95 latency, <1% error rate
```

## Project Complete!

After Phase 7, you have a fully functional inference platform with:
- OpenAI-compatible API
- Authentication and rate limiting
- Priority queuing and streaming
- Full observability (metrics + dashboards + logs)
- Safety filtering
- Circuit breaker and health checks
- Internet accessibility via Cloudflare Tunnel

Read [frontier-lab-mapping.md](../architecture/frontier-lab-mapping.md) to see
how every component maps to what runs at Anthropic/OpenAI scale.
