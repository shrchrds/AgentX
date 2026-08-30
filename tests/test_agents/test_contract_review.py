"""Tests for the ContractReviewAgent.

All LLM calls are mocked with deterministic responses.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage

from app.agents.contract_review import ContractReviewAgent
from app.memory.backends.in_memory import InMemoryStore


def _make_mock_llm(response_text: str = "Contract analysis complete."):
    """Create a mock LLM that returns a fixed response."""
    mock = MagicMock()
    mock.ainvoke = AsyncMock(return_value=AIMessage(content=response_text))
    return mock


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


@pytest.fixture
def agent(store: InMemoryStore):
    return ContractReviewAgent(
        agent_id="cr-test",
        memory=store,
        llm=_make_mock_llm(),
    )


class TestContractReviewAgent:
    """Tests for ContractReviewAgent."""

    async def test_process_input_returns_valid_response(self, agent: ContractReviewAgent) -> None:
        resp = await agent.process_input("task-1", "Review this NDA.", {})
        assert resp.task_id == "task-1"
        assert resp.agent_id == "cr-test"
        assert resp.status == "completed"
        assert resp.output_data == "Contract analysis complete."
        assert resp.errors == []

    async def test_memory_saved_after_processing(
        self, agent: ContractReviewAgent, store: InMemoryStore
    ) -> None:
        await agent.process_input("task-1", "Review contract.", {})
        records = await store.load_context("cr-test", "task-1")
        assert len(records) == 1
        assert records[0].data["role"] == "assistant"

    async def test_llm_failure_returns_failed_response(self, store: InMemoryStore) -> None:
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(side_effect=RuntimeError("API timeout"))
        agent = ContractReviewAgent(agent_id="cr-fail", memory=store, llm=mock_llm)
        resp = await agent.process_input("task-1", "Review contract.", {})
        assert resp.status == "failed"
        assert len(resp.errors) == 1
        assert "RuntimeError" in resp.errors[0]

    async def test_output_is_sanitized(self, store: InMemoryStore) -> None:
        llm = _make_mock_llm("Result <|im_start|> leaked")
        agent = ContractReviewAgent(agent_id="cr-san", memory=store, llm=llm)
        resp = await agent.process_input("task-1", "Test.", {})
        assert "<|im_start|>" not in resp.output_data
