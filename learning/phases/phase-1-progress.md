# Phase 1 Progress: Basic Model Serving

## Status: IN PROGRESS
## Started: 2026-03-19
## Approach: Self-implementation with Claude guidance

## Steps

| # | Step | Status | File(s) |
|---|------|--------|---------|
| 1 | Config system (Pydantic Settings) | DONE | `src/config.py` |
| 2 | App factory + lifespan | DONE | `src/main.py` |
| 3 | Pydantic schemas (OpenAI format) | DONE | `src/api/v1/schemas/chat.py`, `common.py` |
| 4 | Inference service (vLLM proxy) | DONE | `src/services/inference.py` |
| 5a | Global exception handler | DONE | `src/main.py` |
| 5b | Dependency injection for InferenceService | DONE | `src/dependencies.py` |
| 5 | Chat completions endpoint (cleaned up) | DONE | `src/api/v1/chat.py` |
| 6 | Router (plain wiring) | DONE | `src/api/router.py` |
| 7 | Health + models endpoints | DONE | `src/api/v1/health.py`, `src/api/v1/models.py` |
| 8 | Docker Compose (vLLM) | IN PROGRESS | `docker-compose.yml` |
| 9 | Tests | TODO | `tests/conftest.py`, `tests/integration/` |

## Clean Patterns (applied throughout)

- **Global exception handlers** in `main.py` — endpoints never catch errors themselves
- **`Depends()`** for services — endpoints declare what they need, FastAPI provides it
- **Plain router wiring** — `router.py` only connects routers to prefixes, no logic
- **Lifespan for shared resources** — httpx client created once, cleaned up on shutdown

## Recommended Build Order

1. config (DONE) → 2. app factory (DONE) → 3. schemas (DONE) → 4. inference (DONE)
→ 5a. exception handler (DONE) → 5b. dependency injection (DONE) → 5. chat cleanup (DONE)
→ 6. router cleanup (DONE) → 7. health + models (DONE) → 8. docker (IN PROGRESS) → 9. tests

## Verification Checklist

- [ ] `make dev` starts the FastAPI server on :8000
- [ ] `GET /health` returns 200
- [ ] `GET /v1/models` returns model list (with vLLM running)
- [ ] `POST /v1/chat/completions` returns a chat response (with vLLM running)
- [ ] Tests pass: `make test`

## How to Get Help

- Ask Claude to explain any concept deeper
- Ask "why?" about any design decision
- Ask "what if I did X instead?" to explore alternatives
- Share your code for review when you want feedback
- Ask for hints if stuck (not full solutions)
