# Concept: Internet Exposure

## What Is It?

Making your locally-running API accessible from anywhere on the internet,
securely. This involves reverse proxying, SSL/TLS encryption, DNS, and
protection against attacks.

## Why Does It Exist?

Your API is only useful if you (and maybe others) can access it from any device,
anywhere. Without internet exposure:
- Only accessible from your home network
- Can't use it from your phone or another location
- Can't share it with friends or colleagues

## Two Approaches

### Approach 1: Cloudflare Tunnel (Recommended)

```
Your phone (anywhere)
       │
       ▼
[Cloudflare Edge]  ← Global CDN, DDoS protection, free SSL
       │
       │  Encrypted tunnel (outbound from your PC)
       │
       ▼
[cloudflared on your PC]  ← Small daemon running in Docker
       │
       ▼
[nginx → FastAPI → vLLM]  ← Your local stack
```

**How it works**:
1. `cloudflared` runs on your PC and connects OUTBOUND to Cloudflare
2. No incoming ports opened on your router (nothing to hack)
3. Cloudflare provides SSL, DDoS protection, and a domain
4. Traffic flows: Internet → Cloudflare → tunnel → your PC

**Pros**: No port forwarding, free SSL, DDoS protection, easy setup
**Cons**: Requires Cloudflare account and a domain (~$10/year for .dev)

### Approach 2: Port Forwarding + DynDNS (Traditional)

```
Your phone (anywhere)
       │
       ▼
[DNS: myapi.duckdns.org → your home IP]
       │
       ▼
[Your Router]  ← Port 443 forwarded to your PC
       │
       ▼
[nginx → FastAPI → vLLM]  ← Your local stack
```

**Pros**: No third-party dependency, full control
**Cons**: Exposes your home IP, manual SSL (Let's Encrypt), router config varies

## Defense in Depth

Even with auth and rate limiting, add these layers:

```
Layer 1: Cloudflare      → DDoS protection, bot detection
Layer 2: nginx           → Connection limits, request buffering
Layer 3: API Gateway     → Auth, rate limiting
Layer 4: IP allowlist    → Optional: only allow known IPs
Layer 5: Safety filter   → Content-level protection
```

Each layer catches threats the previous one missed.

## Files You'll Build

| File | Purpose |
|------|---------|
| `docker-compose.yml` (cloudflared service) | Tunnel container config |
| `config/nginx/nginx.conf` | SSL termination, reverse proxy |
| `scripts/load_test.py` | Verify performance before exposing |
| `docs/deployment.md` | Setup guide for both approaches |
