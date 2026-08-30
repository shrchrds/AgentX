"""Shared pytest fixtures for AgentX tests."""

import pytest
from httpx import ASGITransport, AsyncClient
from langchain_core.language_models import FakeListChatModel

from app.agents.manager import AgentManager
from app.memory.backends.in_memory import InMemoryStore
from app.orchestrator.graph import AgentOrchestrator


@pytest.fixture
def mock_llm():
    """Returns a FakeListChatModel with deterministic responses."""
    return FakeListChatModel(
        responses=[
            "This is a detailed contract analysis.",
            "This is a comprehensive case analysis.",
            "This is a thorough risk assessment.",
        ]
    )


@pytest.fixture
def memory_store():
    """Returns an InMemoryStore instance."""
    return InMemoryStore()


@pytest.fixture
async def agent_manager(memory_store, mock_llm):
    """Returns an AgentManager with mock LLM."""
    manager = AgentManager(memory_store=memory_store, llm=mock_llm)

    # Patch LLM initialization for all agents
    for agent in manager._registry.values():
        agent._llm = mock_llm

    return manager


@pytest.fixture
async def orchestrator(agent_manager):
    """Returns an AgentOrchestrator wired to the mocked agent manager."""
    return AgentOrchestrator(agent_manager=agent_manager)


@pytest.fixture
async def test_client():
    """Returns an httpx AsyncClient for testing the FastAPI app."""
    from app.main import app
    from app.memory.backends.in_memory import InMemoryStore

    # Initialize app state for tests (mirrors app/main.py lifespan).
    memory_store = InMemoryStore()
    agent_manager = AgentManager(memory_store=memory_store)
    orchestrator = AgentOrchestrator(agent_manager=agent_manager)

    app.state.memory_store = memory_store
    app.state.agent_manager = agent_manager
    app.state.orchestrator = orchestrator
    app.state.task_store = {}
    app.state.log_store = {}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
def api_key():
    """Returns a valid test API key."""
    return "test-api-key-12345"
