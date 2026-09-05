"""Tests for the logs API routes."""

from httpx import AsyncClient


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
