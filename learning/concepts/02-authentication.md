# Concept: API Key Authentication

## What Is It?

Authentication answers: "Who are you?" Every request must prove its identity
by providing an API key. The key determines who you are, what tier you're on,
and what rate limits apply to you.

## Why Does It Exist?

GPU time is expensive. Without authentication:
- Anyone could use your GPU (cost you money / steal your resources)
- You can't rate limit individual users
- You can't track who's doing what
- You can't revoke access to bad actors

## Real-World Analogy

An API key is like a membership card at a gym:
- You show it at the door (include in request header)
- The gym knows who you are and your membership tier
- Different tiers get different privileges (pool access, personal trainer)
- If you violate rules, your card gets deactivated
- The gym never gives you a copy of their member database (hashing)

## How It Works

### The Flow

```
Client                          API Gateway                    Redis
  │                                 │                            │
  │ Authorization: Bearer sk-abc123 │                            │
  │────────────────────────────────>│                            │
  │                                 │ SHA256("sk-abc123")        │
  │                                 │ = "7f3a8b..."             │
  │                                 │                            │
  │                                 │ GET apikey:7f3a8b...      │
  │                                 │───────────────────────────>│
  │                                 │                            │
  │                                 │ {tier:"pro", name:"Alice"} │
  │                                 │<───────────────────────────│
  │                                 │                            │
  │                                 │ Attach to request state    │
  │                    200 OK       │                            │
  │<────────────────────────────────│                            │
```

### Why Hash the Key?

You NEVER store raw API keys. Here's why:

1. User generates key: `sk-abc123def456...` (they save this)
2. You hash it: `SHA256("sk-abc123...") → "7f3a8b..."` (you store this)
3. On every request, hash the incoming key and look up the hash

If your Redis is compromised, attackers get hashes - which are useless.
They can't reverse a SHA-256 hash back to the original key.

This is the same pattern used by GitHub tokens, Stripe API keys, and AWS
access keys.

### API Key Format

Following OpenAI's convention:
```
sk-proj-abc123def456ghi789...
│  │    │
│  │    └── Random bytes (base62 encoded)
│  └── Prefix identifier (optional: proj, test, live)
└── "Secret Key" prefix (industry convention)
```

### Tier System

| Tier | RPM | TPM | Queue Priority | Use Case |
|------|-----|-----|----------------|----------|
| free | 10 | 10,000 | P2 (lowest) | Testing, personal projects |
| pro | 60 | 100,000 | P1 (medium) | Regular usage |
| admin | 300 | 1,000,000 | P0 (highest) | You, the operator |

## Security Considerations

1. **Keys in headers, not URLs**: Query strings appear in logs. Headers don't.
2. **Hash before storing**: Never store plaintext keys.
3. **Show key only once**: When generating a key, display it once. After that,
   only the hash exists. (Like how GitHub shows new tokens once.)
4. **Constant-time comparison**: Use `hmac.compare_digest()` to prevent timing
   attacks when comparing hashes.

## Files You'll Build

| File | Purpose |
|------|---------|
| `src/middleware/auth.py` | Extract and validate API key from header |
| `src/models/api_key.py` | APIKey dataclass with tier info |
| `scripts/generate_api_key.py` | CLI tool to create new keys |
| `scripts/seed_redis.py` | Load development keys into Redis |
| `config/api_keys/keys.yaml` | Development key definitions |
