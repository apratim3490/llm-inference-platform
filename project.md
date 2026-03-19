# LLM Inference Platform ("Mini Anthropic")

## Purpose

A simplified but complete inference infrastructure that serves an LLM (Mistral 7B)
on a local RTX 3090 over the internet. Implements every key concept used by
frontier AI labs: API gateway, auth, rate limiting, queuing, streaming, observability,
safety, and circuit breakers.

## Architecture

See `learning/architecture/overview.md` for full diagrams.

```
Internet → Cloudflare Tunnel → nginx (SSL) → FastAPI API Gateway → vLLM (GPU)
                                                     ↕
                                                   Redis
                                                (auth, queue, rate limits, usage)
```

## Tech Stack

- **Python 3.12** + **FastAPI** - API gateway
- **vLLM** - Model serving (Docker/WSL2)
- **Redis 7** - State store (rate limits, queue, usage)
- **nginx** - Reverse proxy + SSL
- **Prometheus** + **Grafana** - Observability
- **Docker Compose** - Orchestration
- **Cloudflare Tunnel** - Internet exposure

## Hardware

- NVIDIA RTX 3090 (24GB VRAM)
- Mistral 7B Instruct v0.3 (4-bit GPTQ, ~4GB)
- Windows 11 + WSL2

## Build Phases

| Phase | Status | Description |
|-------|--------|-------------|
| 1 | Not Started | Basic model serving + OpenAI-compatible API |
| 2 | Not Started | Authentication, rate limiting, usage tracking |
| 3 | Not Started | Request queuing, streaming (SSE) |
| 4 | Not Started | Observability (Prometheus, Grafana, structured logs) |
| 5 | Not Started | Safety layer (content filtering) |
| 6 | Not Started | Production hardening (circuit breaker, health checks, SSL) |
| 7 | Not Started | Internet exposure (Cloudflare Tunnel) |

## Project Structure

```
llm-inference-platform/
├── learning/          ← Concept docs, phase plans, architecture diagrams
├── src/               ← Application code (what you build)
├── tests/             ← Unit, integration, e2e tests
├── config/            ← nginx, prometheus, grafana, api keys
├── scripts/           ← Utility scripts (key gen, load test, setup)
├── docs/              ← Project documentation
├── docker-compose.yml ← Orchestration
└── project.md         ← This file
```
