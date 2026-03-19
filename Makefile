# LLM Inference Platform - Convenience Commands

.PHONY: help setup dev test lint format up down logs clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ===================
# Development Setup
# ===================

setup: ## Install dependencies in a virtual environment
	python -m venv .venv
	.venv/Scripts/pip install -r requirements-dev.txt

dev: ## Run the API server in development mode
	.venv/Scripts/uvicorn src.main:create_app --factory --reload --host 0.0.0.0 --port 8000

# ===================
# Testing
# ===================

test: ## Run all tests
	.venv/Scripts/pytest tests/ -v

test-unit: ## Run unit tests only
	.venv/Scripts/pytest tests/unit/ -v -m unit

test-integration: ## Run integration tests only
	.venv/Scripts/pytest tests/integration/ -v -m integration

test-coverage: ## Run tests with coverage report
	.venv/Scripts/pytest tests/ --cov=src --cov-report=term-missing

# ===================
# Code Quality
# ===================

lint: ## Run linter (ruff)
	.venv/Scripts/ruff check src/ tests/

format: ## Format code (black + ruff)
	.venv/Scripts/black src/ tests/
	.venv/Scripts/ruff check --fix src/ tests/

typecheck: ## Run type checker (mypy)
	.venv/Scripts/mypy src/

# ===================
# Docker
# ===================

up: ## Start all services
	docker compose up -d

down: ## Stop all services
	docker compose down

logs: ## Tail all service logs
	docker compose logs -f

# ===================
# Utilities
# ===================

generate-key: ## Generate a new API key
	.venv/Scripts/python scripts/generate_api_key.py

seed: ## Seed Redis with development API keys
	.venv/Scripts/python scripts/seed_redis.py

load-test: ## Run load test (10 concurrent, 60 seconds)
	.venv/Scripts/python scripts/load_test.py --concurrency 10 --duration 60

clean: ## Remove build artifacts and caches
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
