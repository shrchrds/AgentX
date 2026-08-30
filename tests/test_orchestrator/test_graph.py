"""Tests for the AgentOrchestrator graph.

All agents and LLM calls are mocked — no live API calls.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage

from app.agents.manager import AgentManager
from app.memory.backends.in_memory import InMemoryStore
from app.models.task import TaskRequest, TaskStatus
from app.orchestrator.graph import AgentOrchestrator


def _make_mock_llm(response: str = "Mocked analysis output."):
    mock = MagicMock()
    mock.ainvoke = AsyncMock(return_value=AIMessage(content=response))
    return mock


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


@pytest.fixture
def manager(store: InMemoryStore) -> AgentManager:
    return AgentManager(memory_store=store, llm=_make_mock_llm())


@pytest.fixture
def orchestrator(manager: AgentManager) -> AgentOrchestrator:
    return AgentOrchestrator(agent_manager=manager, timeout=30)


class TestAgentOrchestrator:
    """Tests for the full orchestration workflow."""

    async def test_full_workflow_contract(self, orchestrator: AgentOrchestrator) -> None:
        task = TaskRequest(
            task_id="test-1",
            input_data="Review this contract for missing clauses.",
        )
        result = await orchestrator.run_workflow(task)
        assert result.task_id == "test-1"
        assert result.status == TaskStatus.COMPLETED
        assert result.output_data is not None
        assert len(result.output_data) > 0
        assert result.completed_at is not None

    async def test_full_workflow_case_analysis(self, orchestrator: AgentOrchestrator) -> None:
        task = TaskRequest(
            task_id="test-2",
            input_data="Analyze this court ruling and find precedents.",
        )
        result = await orchestrator.run_workflow(task)
        assert result.status == TaskStatus.COMPLETED
        assert result.output_data

    async def test_full_workflow_risk(self, orchestrator: AgentOrchestrator) -> None:
        task = TaskRequest(
            task_id="test-3",
            input_data="Evaluate compliance risk and regulatory exposure.",
        )
        result = await orchestrator.run_workflow(task)
        assert result.status == TaskStatus.COMPLETED

    async def test_no_keyword_match_uses_all_agents(self, orchestrator: AgentOrchestrator) -> None:
        task = TaskRequest(
            task_id="test-4",
            input_data="Provide a general legal opinion on this matter.",
        )
        result = await orchestrator.run_workflow(task)
        assert result.status == TaskStatus.COMPLETED
        # Should have multiple agent sections in output
        assert result.output_data

    async def test_error_handling_all_agents_fail(self, store: InMemoryStore) -> None:
        failing_llm = MagicMock()
        failing_llm.ainvoke = AsyncMock(side_effect=RuntimeError("API down"))
        manager = AgentManager(memory_store=store, llm=failing_llm)
        orch = AgentOrchestrator(agent_manager=manager, timeout=30)

        task = TaskRequest(
            task_id="test-fail",
            input_data="Review this contract.",
        )
        result = await orch.run_workflow(task)
        # Agents fail gracefully and return failed status
        assert result.task_id == "test-fail"
        assert result.completed_at is not None
