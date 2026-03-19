# Concept: Circuit Breaker

## What Is It?

A circuit breaker monitors the health of a downstream service (vLLM) and
"trips" when it detects too many failures. While tripped, it immediately
rejects requests with a 503 instead of letting them pile up and time out.

## Why Does It Exist?

Without a circuit breaker, when vLLM crashes or OOMs:
- Every queued request waits for its full timeout (90 seconds)
- 50 requests × 90 seconds = users waiting 90 seconds for an error
- The queue fills up, new requests get 503 anyway
- Even after vLLM recovers, the backed-up queue takes minutes to drain

With a circuit breaker:
- After 5 failures, all new requests immediately get 503 (<1ms)
- Users get fast errors, can retry or go elsewhere
- When vLLM recovers, one probe request confirms it, traffic resumes

## Real-World Analogy

A circuit breaker in your electrical panel:
- Normal: electricity flows to your appliances (requests flow to vLLM)
- Overload: fuse trips, electricity stops (breaker OPENS, requests rejected)
- You fix the problem and flip the breaker back (HALF_OPEN → test → CLOSED)

The breaker protects the rest of the house from a short circuit in one room.

## The Three States

```
          ┌─────────────────────────┐
          │                         │
          ▼                         │
    ┌──────────┐  5 failures  ┌────┴─────┐  30 sec timeout  ┌───────────┐
    │  CLOSED  │─────────────>│   OPEN   │─────────────────>│ HALF_OPEN │
    │ (normal) │              │(fail-fast)│                  │  (probe)  │
    └──────────┘              └──────────┘                  └───────────┘
         ▲                                                       │   │
         │              probe succeeds                           │   │
         └───────────────────────────────────────────────────────┘   │
                                                                     │
                        probe fails → back to OPEN                   │
                        ┌────────────────────────────────────────────┘
                        ▼
                  ┌──────────┐
                  │   OPEN   │
                  └──────────┘
```

### CLOSED (Normal Operation)
- All requests forwarded to vLLM
- Track success/failure of each request
- If failure count exceeds threshold → switch to OPEN

### OPEN (Fast-Fail Mode)
- ALL requests immediately rejected with 503
- No requests sent to vLLM (it's probably down)
- After a timeout period (30 seconds) → switch to HALF_OPEN

### HALF_OPEN (Probing Recovery)
- Allow ONE request through to vLLM
- If it succeeds → switch to CLOSED (recovered!)
- If it fails → switch back to OPEN (still broken)

## Configuration

```python
FAILURE_THRESHOLD = 5       # How many failures before opening
RECOVERY_TIMEOUT = 30       # Seconds before trying HALF_OPEN
ERROR_RATE_THRESHOLD = 0.5  # Open if >50% of recent requests fail
WINDOW_SIZE = 60            # Seconds to look back for error rate
```

## Why Not Just Retry?

Retries CAUSE cascading failures:

```
Without circuit breaker:
  vLLM crashes → 100 requests retry 3 times each → 300 requests hit
  a recovering vLLM → it crashes again → infinite crash loop

With circuit breaker:
  vLLM crashes → 5 requests fail → breaker OPENS → 95 requests get
  instant 503 → vLLM has breathing room to recover → one probe
  succeeds → traffic resumes gradually
```

## Files You'll Build

| File | Purpose |
|------|---------|
| `src/services/circuit_breaker.py` | Three-state circuit breaker class |
| `src/models/enums.py` | CircuitState enum |
| `tests/unit/test_circuit_breaker.py` | State transition testing |
