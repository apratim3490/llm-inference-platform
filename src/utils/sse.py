"""
Server-Sent Events (SSE) Helpers

Formats streaming tokens as SSE events in OpenAI-compatible format:
  data: {"choices":[{"delta":{"content":"token"}}]}\n\n

Handles client disconnect detection to stop wasting GPU cycles.
"""

# TODO: Phase 3 - format_sse_event() helper
# TODO: Phase 3 - streaming generator with disconnect detection
# TODO: Phase 3 - format [DONE] termination event
