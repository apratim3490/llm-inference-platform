"""
Shared Test Fixtures

Provides:
- FastAPI test client (httpx.AsyncClient)
- Mock vLLM responses (respx)

Built incrementally as each phase adds new components.
"""

import pytest
import respx
import httpx
from httpx import ASGITransport, Response

from src.main import app


FAKE_CHAT_RESPONSE = {
    "id": "chatcmpl-test",
    "object": "chat.completion",
    "created": 1234567890,
    "model": "RedHatAI/Mistral-7B-Instruct-v0.3-GPTQ-4bit",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": "Hello!"},
            "finish_reason": "stop",
        }
    ],
    "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
}

FAKE_MODELS_RESPONSE = {
    "object": "list",
    "data": [
        {
            "id": "RedHatAI/Mistral-7B-Instruct-v0.3-GPTQ-4bit",
            "object": "model",
            "owned_by": "vllm",
        }
    ],
}


@pytest.fixture
def test_app():
    app.state.http_client = httpx.AsyncClient(
        base_url="http://localhost:8001",
        timeout=10.0,
    )
    return app


@pytest.fixture
def mock_vllm():
    with respx.mock(base_url="http://localhost:8001", assert_all_called=False) as respx_mock:
        respx_mock.post("/v1/chat/completions").mock(
            return_value=Response(200, json=FAKE_CHAT_RESPONSE)
        )
        respx_mock.get("/v1/models").mock(
            return_value=Response(200, json=FAKE_MODELS_RESPONSE)
        )
        respx_mock.get("/health").mock(
            return_value=Response(200, json={"status": "ok"})
        )
        yield respx_mock


@pytest.fixture
async def client(test_app, mock_vllm):
    async with httpx.AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as test_client:
        yield test_client


# TODO: Phase 2 - FakeRedis fixture
# TODO: Phase 2 - Test API key fixtures
