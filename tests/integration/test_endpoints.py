"""
Integration Tests - Phase 1 Endpoints

Tests all Phase 1 endpoints by mocking vLLM with respx.
No real GPU or model needed - the mock intercepts HTTP calls.
"""

import httpx
import pytest
import respx
from httpx import Response


VALID_CHAT_BODY = {
    "model": "RedHatAI/Mistral-7B-Instruct-v0.3-GPTQ-4bit",
    "messages": [{"role": "user", "content": "Say hello"}],
}


# ---- Health ----


@pytest.mark.integration
async def test_health_returns_200(client):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


# ---- Chat Completions ----


@pytest.mark.integration
async def test_chat_completion_success(client):
    response = await client.post("/v1/chat/completions", json=VALID_CHAT_BODY)

    assert response.status_code == 200
    data = response.json()
    assert "choices" in data
    assert data["choices"][0]["message"]["content"] == "Hello!"
    assert data["usage"]["total_tokens"] == 15


@pytest.mark.integration
async def test_chat_missing_messages(client):
    response = await client.post(
        "/v1/chat/completions",
        json={"model": "test-model"},
    )

    assert response.status_code == 422


@pytest.mark.integration
async def test_chat_empty_messages(client):
    response = await client.post(
        "/v1/chat/completions",
        json={"model": "test-model", "messages": []},
    )

    assert response.status_code == 422


@pytest.mark.integration
async def test_chat_missing_model(client):
    response = await client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "hi"}]},
    )

    assert response.status_code == 422


@pytest.mark.integration
async def test_chat_invalid_temperature(client):
    body = {**VALID_CHAT_BODY, "temperature": 3.0}
    response = await client.post("/v1/chat/completions", json=body)

    assert response.status_code == 422


@pytest.mark.integration
async def test_vllm_timeout(client, mock_vllm):
    def raise_timeout(request):
        raise httpx.TimeoutException("timed out")

    mock_vllm.post("/v1/chat/completions").mock(side_effect=raise_timeout)

    response = await client.post("/v1/chat/completions", json=VALID_CHAT_BODY)

    assert response.status_code == 504
    assert "timed out" in response.json()["error"].lower()


@pytest.mark.integration
async def test_vllm_unavailable(client, mock_vllm):
    def raise_connect_error(request):
        raise httpx.ConnectError("connection refused")

    mock_vllm.post("/v1/chat/completions").mock(side_effect=raise_connect_error)

    response = await client.post("/v1/chat/completions", json=VALID_CHAT_BODY)

    assert response.status_code == 503
    assert "unavailable" in response.json()["error"].lower()


@pytest.mark.integration
async def test_vllm_returns_500(client, mock_vllm):
    mock_vllm.post("/v1/chat/completions").mock(
        return_value=Response(500, json={"error": "internal error"})
    )

    response = await client.post("/v1/chat/completions", json=VALID_CHAT_BODY)

    assert response.status_code == 502


# ---- Models ----


@pytest.mark.integration
async def test_list_models_success(client):
    response = await client.get("/v1/models")

    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == "RedHatAI/Mistral-7B-Instruct-v0.3-GPTQ-4bit"


@pytest.mark.integration
async def test_list_models_vllm_down(client, mock_vllm):
    def raise_connect_error(request):
        raise httpx.ConnectError("connection refused")

    mock_vllm.get("/v1/models").mock(side_effect=raise_connect_error)

    response = await client.get("/v1/models")

    assert response.status_code == 503
