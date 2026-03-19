# Learning Guide - LLM Inference Platform

## What Is This?

You're building a simplified version of the inference infrastructure that frontier AI labs
(Anthropic, OpenAI, Google DeepMind) use to serve LLMs to millions of users. Every component
in this project maps to a real production concept used at massive scale.

## How to Use This Folder

```
learning/
├── architecture/       ← System design, diagrams, how it all fits together
│   ├── overview.md     ← Start here - the big picture
│   ├── request-lifecycle.md  ← Follow a request from curl to GPU and back
│   └── frontier-lab-mapping.md  ← What you build vs what Anthropic runs
│
├── concepts/           ← Deep dives into each infrastructure concept
│   ├── 01-api-gateway.md
│   ├── 02-authentication.md
│   ├── 03-rate-limiting.md
│   ├── 04-request-queuing.md
│   ├── 05-model-serving.md
│   ├── 06-streaming-sse.md
│   ├── 07-usage-tracking.md
│   ├── 08-safety-layer.md
│   ├── 09-circuit-breaker.md
│   ├── 10-observability.md
│   ├── 11-health-checks.md
│   └── 12-internet-exposure.md
│
└── phases/             ← Step-by-step build plan for each phase
    ├── phase-1-basic-serving.md
    ├── phase-2-auth-and-limits.md
    ├── phase-3-queue-and-streaming.md
    ├── phase-4-observability.md
    ├── phase-5-safety.md
    ├── phase-6-hardening.md
    └── phase-7-internet.md
```

## Recommended Learning Path

1. Read `architecture/overview.md` to understand the big picture
2. Read `architecture/request-lifecycle.md` to see how a request flows
3. Start Phase 1 - read the phase doc, then the relevant concept docs
4. Build the code, verify it works, then move to Phase 2
5. After all phases, read `architecture/frontier-lab-mapping.md` for the full picture

## Your Hardware

- **GPU**: NVIDIA RTX 3090 (24GB VRAM)
- **OS**: Windows 11 with WSL2
- **Model**: Mistral 7B Instruct v0.3 (4-bit quantized, ~4GB VRAM)
