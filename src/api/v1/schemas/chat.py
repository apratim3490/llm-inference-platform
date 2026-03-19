"""
Chat Completion Request/Response Schemas

Pydantic models matching the OpenAI chat completions format.
Every field is validated automatically - bad requests never reach the GPU.
"""

# TODO: Phase 1 - ChatMessage model
#   Fields: role (Literal["system", "user", "assistant"]), content (str)
#   Hint: Literal from typing restricts to exact string values
#
# TODO: Phase 1 - ChatCompletionRequest model
#   Fields:
#     model (str) - required
#     messages (list[ChatMessage]) - required, min 1 item
#     max_tokens (int) - default 512, range 1-4096
#     temperature (float) - default 0.7, range 0.0-2.0
#     top_p (float) - default 1.0, range 0.0-1.0
#     stream (bool) - default False
#     stop (list[str] | str | None) - default None
#   Hints:
#     - Use Field(..., min_length=1) for required list with minimum
#     - Use Field(default=512, ge=1, le=4096) for bounded integers
#
# TODO: Phase 1 - Choice model
#   Fields: index (int, default 0), message (ChatMessage), finish_reason (str | None)
#
# TODO: Phase 1 - ChatCompletionResponse model
#   Fields:
#     id (str) - auto-generated like "chatcmpl-abc123"
#     object (str) - always "chat.completion"
#     created (int) - unix timestamp
#     model (str)
#     choices (list[Choice])
#     usage (UsageInfo)
#   Hints:
#     - Use Field(default_factory=lambda: ...) for dynamic defaults
#     - uuid.uuid4().hex[:12] generates a short unique ID
#     - int(time.time()) gives unix timestamp
