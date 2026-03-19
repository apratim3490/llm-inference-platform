# Concept: Safety Layer (Content Filtering)

## What Is It?

The safety layer inspects user inputs AND model outputs to prevent harmful content.
It sits in the request pipeline twice: before inference (input filter) and after
inference (output filter).

## Why Does It Exist?

LLMs can be prompted to generate harmful content. Without safety filtering:
- Users could request instructions for dangerous activities
- The model might output personal information from training data
- Prompt injection could bypass system instructions
- You could be legally liable for harmful outputs

## Real-World Analogy

Think of content moderation on social media:
- Posts are scanned before publishing (input filter)
- Published content is monitored for violations (output filter)
- Different categories of violations (hate speech, violence, PII)
- Automated system catches most violations, edge cases need human review

For your API: the "posts" are user prompts and model responses.

## Two Stages

### Input Filtering (Pre-Inference)

Check user messages BEFORE spending GPU time:

```
User: "How do I hack into my neighbor's WiFi?"
  → Category: potentially_harmful
  → Action: BLOCK (400 error, no GPU used)

User: "Explain how WiFi encryption works"
  → Category: safe
  → Action: PASS (proceed to inference)
```

### Output Filtering (Post-Inference)

Check model responses BEFORE sending to user:

```
Model output: "The capital of France is Paris."
  → Category: safe
  → Action: SEND to user

Model output: "Here's a Social Security number: 123-45-6789"
  → Category: personal_info (PII leak)
  → Action: BLOCK, return error, log incident
```

## Implementation Layers

### Layer 1: Keyword Blocklist (Simple, Fast)
```python
BLOCKED_PATTERNS = [
    r"\b(hack|exploit)\s+(into|password)",
    r"\d{3}-\d{2}-\d{4}",  # SSN pattern
    r"\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}",  # Credit card
]
```
- Pros: <1ms, no false positives on exact matches, easy to update
- Cons: Easy to bypass, can't understand context

### Layer 2: Pattern-Based Classification (Medium)
```python
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(previous|above|all)\s+instructions",
    r"you\s+are\s+now\s+(DAN|jailbroken|unrestricted)",
    r"system\s*:\s*you\s+are",  # attempting to inject system prompt
]
```
- Pros: Catches common attack patterns, still fast
- Cons: Arms race with attackers

### Layer 3: ML Classifier (Optional, Sophisticated)
```python
# Small CPU-based toxic content classifier
from transformers import pipeline
classifier = pipeline("text-classification", model="unitary/toxic-bert")
result = classifier("some text")
# → {"label": "toxic", "score": 0.92}
```
- Pros: Understands context, catches subtle violations
- Cons: ~10ms latency, potential false positives, needs a model

## Streaming Safety Challenge

Output filtering during streaming is tricky:

```
Token 1: "The"     → safe? Incomplete, buffer it
Token 2: "secret"  → safe? Still incomplete
Token 3: "to"      → safe? Still buffering...
Token 4: "good"    → "The secret to good" → SAFE, release buffer
Token 5: "cooking" → safe, send immediately
```

Strategy: Buffer N tokens, check the buffer, release tokens that are confirmed safe.
This adds a small delay but prevents unsafe partial content from reaching the user.

## What Frontier Labs Do Differently

| Yours | Frontier Lab |
|-------|-------------|
| Keyword + regex | Multi-model classifier pipeline |
| Optional CPU classifier | Dedicated GPU safety models |
| Binary safe/unsafe | Risk scores with thresholds per category |
| Block or pass | Block, warn, flag for human review, modify |
| Same model for all users | Per-customer safety policies |

Additionally: Constitutional AI (Anthropic), RLHF safety training, red team testing.

## Files You'll Build

| File | Purpose |
|------|---------|
| `src/services/safety.py` | SafetyFilter class with input/output checking |
| `config/safety/blocklist.yaml` | Configurable blocked patterns |
| `tests/unit/test_safety.py` | Verify detection accuracy |
