"""
Safety Filter (Content Filtering)

Inspects user inputs and model outputs for harmful content.
Sits in the pipeline twice: pre-inference (input) and post-inference (output).

Layers:
1. Keyword/regex blocklist (fast, simple)
2. PII detection (SSN, credit card patterns)
3. Prompt injection detection
4. Optional ML classifier (CPU-based)
"""

# TODO: Phase 5 - SafetyFilter class
# TODO: Phase 5 - check_input() and check_output() methods
# TODO: Phase 5 - SafetyResult dataclass
