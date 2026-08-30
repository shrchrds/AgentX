"""Tests for the logs API routes."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from langchain_core.messages import AIMessage

from app.main import app


def _make_mock_llm():
    mock = MagicMock()
    mock.ainvoke = AsyncMock(return_value=AIMessage(content="Mocked."))
    return mock


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        if hasattr(app.state, "agent_manager"):
            for agent_id in list(app.state.agent_manager._registry.keys()):
                agent = app.state.agent_manager._registry[agent_id]
                agent._llm = _make_mock_llm()
        yield c


class TestLogRoutes:
    """Tests for GET /logs/{task_id}."""

    async def test_get_logs_after_task(self, client: AsyncClient) -> None:
        # Create a task first to generate logs
        create_resp = await client.post(
            "/api/v1/tasks",
            json={"input_data": "Review this contract."},
            headers={"X-API-Key": "test-key"},
        )
        task_id = create_resp.json()["task_id"]

        # Retrieve logs
        resp = await client.get(
            f"/api/v1/logs/{task_id}",
            headers={"X-API-Key": "test-key"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == task_id
        assert isinstance(data["logs"], list)
        assert len(data["logs"]) >= 2  # submit + complete

    async def test_get_logs_not_found(self, client: AsyncClient) -> None:
        resp = await client.get(
            "/api/v1/logs/nonexistent",
            headers={"X-API-Key": "test-key"},
        )
        assert resp.status_code == 404
