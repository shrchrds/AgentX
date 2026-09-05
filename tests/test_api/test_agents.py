"""Tests for the agent API routes."""

from __future__ import annotations

from httpx import AsyncClient


class TestAgentRoutes:
    """Tests for GET /agents and POST /agents."""

    async def test_list_agents(self, client: AsyncClient) -> None:
        resp = await client.get(
            "/api/v1/agents",
            headers={"X-API-Key": "test-key"},
        )
        assert resp.status_code == 200
        agents = resp.json()
        assert isinstance(agents, list)
        assert len(agents) >= 3  # Default agents

    async def test_register_agent(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/agents",
            json={"agent_type": "contract_review", "agent_id": "api-test-cr"},
            headers={"X-API-Key": "test-key"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["agent_id"] == "api-test-cr"
        assert data["agent_type"] == "contract_review"

    async def test_register_invalid_type(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/agents",
            json={"agent_type": "invalid_type"},
            headers={"X-API-Key": "test-key"},
        )
        assert resp.status_code == 422

    async def test_list_agents_no_auth(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/agents")
        assert resp.status_code == 422  # Missing required header
