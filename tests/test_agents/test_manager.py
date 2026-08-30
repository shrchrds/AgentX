"""Tests for the AgentManager."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage

from app.agents.manager import AgentManager
from app.memory.backends.in_memory import InMemoryStore
from app.models.agent import AgentType


def _make_mock_llm():
    mock = MagicMock()
    mock.ainvoke = AsyncMock(return_value=AIMessage(content="test"))
    return mock


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


@pytest.fixture
def manager(store: InMemoryStore) -> AgentManager:
    return AgentManager(memory_store=store, llm=_make_mock_llm())


class TestAgentManager:
    """Tests for agent registry and lifecycle."""

    def test_default_agents_registered(self, manager: AgentManager) -> None:
        agents = manager.list_agents()
        assert len(agents) == 3
        types = {a.agent_type for a in agents}
        assert types == {
            AgentType.CONTRACT_REVIEW,
            AgentType.CASE_ANALYSIS,
            AgentType.RISK_ANALYSIS,
        }

    def test_register_new_agent(self, manager: AgentManager) -> None:
        info = manager.register_agent(AgentType.CONTRACT_REVIEW, agent_id="custom-cr")
        assert info.agent_id == "custom-cr"
        assert info.agent_type == AgentType.CONTRACT_REVIEW
        assert len(manager.list_agents()) == 4

    def test_register_duplicate_id_raises(self, manager: AgentManager) -> None:
        manager.register_agent(AgentType.CONTRACT_REVIEW, agent_id="dup-1")
        with pytest.raises(KeyError, match="dup-1"):
            manager.register_agent(AgentType.CASE_ANALYSIS, agent_id="dup-1")

    def test_get_agent(self, manager: AgentManager) -> None:
        manager.register_agent(AgentType.RISK_ANALYSIS, agent_id="get-test")
        agent = manager.get_agent("get-test")
        assert agent.agent_id == "get-test"

    def test_get_missing_agent_raises(self, manager: AgentManager) -> None:
        with pytest.raises(KeyError, match="nonexistent"):
            manager.get_agent("nonexistent")

    def test_remove_agent(self, manager: AgentManager) -> None:
        manager.register_agent(AgentType.CONTRACT_REVIEW, agent_id="remove-me")
        initial_count = len(manager.list_agents())
        manager.remove_agent("remove-me")
        assert len(manager.list_agents()) == initial_count - 1

    def test_remove_missing_agent_raises(self, manager: AgentManager) -> None:
        with pytest.raises(KeyError):
            manager.remove_agent("nonexistent")

    def test_get_agents_for_contract_task(self, manager: AgentManager) -> None:
        agents = manager.get_agents_for_task("Review this NDA contract agreement.")
        assert any(a.agent_type == AgentType.CONTRACT_REVIEW for a in agents)

    def test_get_agents_for_case_task(self, manager: AgentManager) -> None:
        agents = manager.get_agents_for_task("Analyze the court ruling and precedent.")
        assert any(a.agent_type == AgentType.CASE_ANALYSIS for a in agents)

    def test_get_agents_for_risk_task(self, manager: AgentManager) -> None:
        agents = manager.get_agents_for_task("Evaluate compliance risk exposure.")
        assert any(a.agent_type == AgentType.RISK_ANALYSIS for a in agents)

    def test_get_agents_no_match_returns_all(self, manager: AgentManager) -> None:
        agents = manager.get_agents_for_task("Something completely different and unrelated.")
        assert len(agents) == len(manager.list_agents())

    def test_auto_generated_agent_id(self, manager: AgentManager) -> None:
        info = manager.register_agent(AgentType.CONTRACT_REVIEW)
        assert info.agent_id.startswith("contract_review-")
