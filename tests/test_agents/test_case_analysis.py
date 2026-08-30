"""Tests for the CaseAnalysisAgent."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage

from app.agents.case_analysis import CaseAnalysisAgent
from app.memory.backends.in_memory import InMemoryStore


def _make_mock_llm(response_text: str = "Case analysis complete."):
    mock = MagicMock()
    mock.ainvoke = AsyncMock(return_value=AIMessage(content=response_text))
    return mock


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


@pytest.fixture
def agent(store: InMemoryStore):
    return CaseAnalysisAgent(agent_id="ca-test", memory=store, llm=_make_mock_llm())


class TestCaseAnalysisAgent:
    """Tests for CaseAnalysisAgent."""

    async def test_process_input_returns_valid_response(self, agent: CaseAnalysisAgent) -> None:
        resp = await agent.process_input("task-1", "Analyze this case.", {})
        assert resp.task_id == "task-1"
        assert resp.status == "completed"
        assert resp.output_data == "Case analysis complete."

    async def test_memory_saved(self, agent: CaseAnalysisAgent, store: InMemoryStore) -> None:
        await agent.process_input("task-1", "Analyze case.", {})
        records = await store.load_context("ca-test", "task-1")
        assert len(records) == 1

    async def test_llm_failure(self, store: InMemoryStore) -> None:
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(side_effect=RuntimeError("API error"))
        agent = CaseAnalysisAgent(agent_id="ca-fail", memory=store, llm=mock_llm)
        resp = await agent.process_input("task-1", "Test.", {})
        assert resp.status == "failed"
        assert len(resp.errors) == 1
