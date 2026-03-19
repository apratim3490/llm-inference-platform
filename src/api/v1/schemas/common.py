"""
Shared Schema Types

Usage info, error responses, model info - used across multiple endpoints.
These are the building blocks that other schemas compose together.
"""

# TODO: Phase 1 - UsageInfo model
#   Fields: prompt_tokens (int), completion_tokens (int), total_tokens (int)
#   This is the data billing systems use to charge users.
#
# TODO: Phase 1 - ErrorResponse model
#   Fields: error (str), message (str), status_code (int)
#   Matches OpenAI's error envelope so SDK clients handle errors correctly.
#
# TODO: Phase 1 - ModelInfo model
#   Fields: id (str), object (str, default "model"), owned_by (str, default "local")
#
# TODO: Phase 1 - ModelListResponse model
#   Fields: object (str, default "list"), data (list[ModelInfo])
#
# Hints:
#   - All models inherit from pydantic.BaseModel
#   - Use type hints for every field
#   - Defaults let you omit fields in responses
