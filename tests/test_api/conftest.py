"""Fixtures for API testing."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from langchain_core.messages import AIMessage

from app.main import app, lifespan


@pytest.fixture
def mock_agent_llm():
    """Returns a mock LLM that generates valid responses."""
    mock = MagicMock()
    mock.ainvoke = AsyncMock(
        return_value=AIMessage(
            content=(
                "### Legal Analysis\n\n"
                "- No material risks identified.\n"
                "- Complies with applicable law."
            )
        )
    )
    return mock


@pytest.fixture
async def client(mock_agent_llm):
    """Async test client with active lifespan and mocked LLM for all agents."""
    async with lifespan(app):
        # Patch all registered agents to use mock LLM so no external calls occur during tests
        for agent in app.state.agent_manager._registry.values():
            agent._llm = mock_agent_llm
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c
