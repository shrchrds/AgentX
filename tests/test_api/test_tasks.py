"""Tests for the task API routes."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from langchain_core.messages import AIMessage

from app.main import app


def _make_mock_llm():
    mock = MagicMock()
    mock.ainvoke = AsyncMock(return_value=AIMessage(content="Mocked analysis."))
    return mock


@pytest.fixture
async def client():
    """Create an async test client with mocked LLM."""
    # Inject mock LLM into the app's agent manager after startup
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        # Patch all agents to use mock LLM
        if hasattr(app.state, "agent_manager"):
            for agent_id in list(app.state.agent_manager._registry.keys()):
                agent = app.state.agent_manager._registry[agent_id]
                agent._llm = _make_mock_llm()
        yield c


class TestTaskRoutes:
    """Tests for POST /tasks and GET /tasks/{id}."""

    async def test_create_task_success(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/tasks",
            json={"input_data": "Review this contract for missing clauses."},
            headers={"X-API-Key": "test-key"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("completed", "failed")
        assert "task_id" in data

    async def test_create_task_no_api_key(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/tasks",
            json={"input_data": "Test input."},
        )
        assert resp.status_code == 422  # Missing required header

    async def test_create_task_invalid_input(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/tasks",
            json={"input_data": ""},
            headers={"X-API-Key": "test-key"},
        )
        assert resp.status_code == 422

    async def test_get_task_success(self, client: AsyncClient) -> None:
        # First create a task
        create_resp = await client.post(
            "/api/v1/tasks",
            json={"input_data": "Review this NDA contract."},
            headers={"X-API-Key": "test-key"},
        )
        task_id = create_resp.json()["task_id"]

        # Then retrieve it
        get_resp = await client.get(
            f"/api/v1/tasks/{task_id}",
            headers={"X-API-Key": "test-key"},
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["task_id"] == task_id

    async def test_get_task_not_found(self, client: AsyncClient) -> None:
        resp = await client.get(
            "/api/v1/tasks/nonexistent-id",
            headers={"X-API-Key": "test-key"},
        )
        assert resp.status_code == 404
