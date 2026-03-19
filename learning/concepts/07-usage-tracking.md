# Concept: Usage Tracking

## What Is It?

Usage tracking counts every token consumed by every API key on every request.
It's the foundation of the billing system - without it, you can't charge users
or understand your costs.

## Why Does It Exist?

GPU time costs real money. Usage tracking answers:
- How much did each user consume today/this month?
- What's my total GPU cost?
- Which users are approaching their limits?
- What's the average request size?

## Real-World Analogy

Think of your electric meter:
- It counts every kilowatt-hour you use
- The utility company reads it monthly
- Your bill = usage × rate
- You can check your usage anytime

For LLMs: tokens are the kilowatt-hours, the API key is your account.

## What Gets Tracked

Every request produces a usage record:

```json
{
  "request_id": "req_a1b2c3d4...",
  "api_key_hash": "7f3a8b...",
  "model": "mistral-7b",
  "input_tokens": 127,
  "output_tokens": 89,
  "total_tokens": 216,
  "latency_ms": 1240,
  "time_to_first_token_ms": 195,
  "stream": true,
  "status": "success",
  "timestamp": "2026-03-18T14:30:00Z"
}
```

### Why Separate Input and Output Tokens?

Frontier labs charge differently for input vs output:
- **Input tokens**: Cheap. The GPU processes them in one pass (the "prefill" step).
- **Output tokens**: Expensive. The GPU generates them one at a time, sequentially.

Typical pricing ratio: output tokens cost 3-5x more than input tokens.

## Storage Strategy

### Per-Request Records (Detailed)
```
Redis List: usage:detail:2026-03-18
→ [record1_json, record2_json, ...]
```

### Per-Key Daily Totals (Aggregated)
```
Redis Hash: usage:daily:sk_hash:2026-03-18
→ {
    "input_tokens": 45230,
    "output_tokens": 31420,
    "total_tokens": 76650,
    "request_count": 342,
    "total_latency_ms": 425600
  }
```

### Why Both?

- **Detailed records**: For debugging, audit trails, per-request billing
- **Daily totals**: For dashboards, usage alerts, monthly invoicing
- Redis INCR is O(1) and atomic - perfect for counters

## Billing Concepts

Even though you're not actually billing anyone, understanding the pattern:

```
Monthly bill for API key sk-abc123:
  Input tokens:  1,250,000 × $0.003/1K = $3.75
  Output tokens:    890,000 × $0.015/1K = $13.35
  Total: $17.10
```

This is exactly how Anthropic and OpenAI compute your bill.

## Files You'll Build

| File | Purpose |
|------|---------|
| `src/services/usage_tracker.py` | Record per-request usage, maintain daily totals |
| `src/utils/token_counter.py` | Count tokens using tiktoken |
| `src/models/usage.py` | UsageRecord dataclass |
| `tests/unit/test_usage_tracker.py` | Verify counting accuracy |
