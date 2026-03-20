# Phase 5: Safety Layer

## Goal

Add input and output content filtering. After this phase, harmful content is
blocked before reaching the GPU (input) and before reaching the user (output).

## What You'll Learn

- Content safety architecture (pre and post inference)
- Keyword and regex-based filtering
- PII detection patterns (SSN, credit cards)
- Prompt injection detection
- Optional ML-based classification
- Streaming safety challenges (buffering tokens)

## Concept Docs to Read First

- [08-safety-layer.md](../concepts/08-safety-layer.md)

## Clean Approach Notes

- **Safety as a `Depends()` dependency**, not middleware. It should only run on
  chat endpoints, not `/health` or `/metrics`.
- **Load blocklist patterns at startup** (lifespan or `lru_cache`), not per-request.
  Reading YAML on every request is wasteful.
- **Skip ML classifier** unless you want the learning exercise. Keyword/regex + PII
  detection covers 90% of cases with zero latency overhead.
- **Custom `SafetyError` exception** handled by global exception handler in `main.py`.

## Steps

### Step 1: Safety Filter Architecture
**File**: `src/services/safety.py`

SafetyFilter class with `check_input()` and `check_output()` methods.
Load patterns once at startup via `lru_cache` or lifespan.

### Step 2: Keyword + Regex Filter
Configurable blocklist from YAML. Categories: violence, PII, prompt injection.

### Step 3: Safety as Dependency
**File**: `src/dependencies.py`

Clean pattern:
```python
async def check_safety(
    body: ChatCompletionRequest,
    safety: SafetyFilter = Depends(get_safety_filter),
) -> ChatCompletionRequest:
    result = safety.check_input(body.messages)
    if not result.safe:
        raise SafetyError(result.category, result.reason)
    return body
```

### Step 4: Optional ML Classifier
CPU-based toxic-bert integration. Disabled by default, enabled via config.
(Optional learning exercise — not required for a clean system.)

### Step 5: Safety Metrics
Add Prometheus counters for filter triggers by category and direction.

### Step 6: Tests
Test detection accuracy for each pattern category.

## Verification

```bash
# Blocked input
curl -X POST ... -d '{"messages":[{"role":"user","content":"my SSN is 123-45-6789"}]}'
# → 400 {"error":"content_filter","category":"personal_info"}

# Safe input passes through
curl -X POST ... -d '{"messages":[{"role":"user","content":"What is TCP?"}]}'
# → 200 with normal response
```
