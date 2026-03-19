"""
Request ID Middleware

Assigns a unique UUID to every request. This ID appears in:
- Response header: X-Request-ID
- Every log line for this request
- Metrics labels
- Error messages

This is how you trace a single request through the entire system.
"""

# TODO: Phase 2 - Implement RequestIDMiddleware
