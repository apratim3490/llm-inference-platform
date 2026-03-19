"""
Authentication Middleware

Extracts API key from Authorization: Bearer header, hashes it,
looks it up in Redis, and attaches key metadata to the request.

Returns 401 if key is missing or invalid.
"""

# TODO: Phase 2 - Implement AuthMiddleware
# TODO: Phase 2 - SHA-256 hashing
# TODO: Phase 2 - Redis lookup
# TODO: Phase 2 - Skip auth for /health, /ready, /docs
