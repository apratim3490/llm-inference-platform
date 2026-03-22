"""
Application Configuration (Pydantic Settings)

All configuration loaded from environment variables.
Follows the 12-factor app methodology: config in the environment, not in code.

Phase 1: vLLM connection settings, API host/port.
Phase 2+: Redis URL, rate limit values, safety settings.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    vllm_base_url: str = "http://localhost:8001"
    vllm_model_name: str = "RedHatAI/Mistral-7B-Instruct-v0.3-GPTQ-4bit"
    vllm_timeout_seconds: float = 90.0
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_env: str = "DEV"
    version: str = "0.1.0"
    completion_url: str = "/v1/chat/completions"
    list_models_url: str = "/v1/models"
    debug: bool = False
    model_config = {
          "env_file": ".env",
          "env_file_encoding": "utf-8",
          "case_sensitive": False,
    }

@lru_cache
def get_settings() -> Settings:
    return Settings()
