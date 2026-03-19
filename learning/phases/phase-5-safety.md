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

## Steps

### Step 1: Safety Filter Architecture
**File**: `src/services/safety.py`

SafetyFilter class with `check_input()` and `check_output()` methods.

### Step 2: Keyword + Regex Filter
Configurable blocklist from YAML. Categories: violence, PII, prompt injection.

### Step 3: Optional ML Classifier
CPU-based toxic-bert integration. Disabled by default, enabled via config.

### Step 4: Pipeline Integration
Wire into chat endpoint: input check before queue, output check during/after generation.

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
