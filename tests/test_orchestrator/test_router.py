"""Tests for the TaskRouter."""

from __future__ import annotations

from app.models.agent import AgentType
from app.orchestrator.router import TaskRouter
from app.orchestrator.state import WorkflowState


class TestTaskRouter:
    """Tests for task classification and routing logic."""

    def test_contract_keywords(self) -> None:
        types = TaskRouter.classify_task("Review this NDA contract.")
        assert AgentType.CONTRACT_REVIEW in types

    def test_case_keywords(self) -> None:
        types = TaskRouter.classify_task("Analyze the court ruling and precedent.")
        assert AgentType.CASE_ANALYSIS in types

    def test_risk_keywords(self) -> None:
        types = TaskRouter.classify_task("Evaluate compliance risk exposure.")
        assert AgentType.RISK_ANALYSIS in types

    def test_multiple_keyword_matches(self) -> None:
        types = TaskRouter.classify_task("Review the contract and assess compliance risk.")
        assert AgentType.CONTRACT_REVIEW in types
        assert AgentType.RISK_ANALYSIS in types

    def test_no_match_returns_all(self) -> None:
        types = TaskRouter.classify_task("Something completely unrelated.")
        assert set(types) == set(AgentType)

    def test_metadata_routing_hint(self) -> None:
        types = TaskRouter.classify_task(
            "Unrelated text.", metadata={"agent_type": "contract_review"}
        )
        assert types == [AgentType.CONTRACT_REVIEW]

    def test_invalid_metadata_hint_falls_through(self) -> None:
        types = TaskRouter.classify_task(
            "Review this contract.", metadata={"agent_type": "invalid_type"}
        )
        # Should fall through to keyword matching
        assert AgentType.CONTRACT_REVIEW in types

    def test_case_insensitive(self) -> None:
        types = TaskRouter.classify_task("REVIEW THE CONTRACT TERMS.")
        assert AgentType.CONTRACT_REVIEW in types


class TestShouldContinue:
    """Tests for the should_continue routing decision."""

    def test_no_errors_routes_to_aggregate(self) -> None:
        state = WorkflowState(
            agent_outputs=[{"output": "data"}],
            errors=[],
        )
        assert TaskRouter.should_continue(state) == "aggregate"

    def test_errors_with_outputs_routes_to_aggregate(self) -> None:
        state = WorkflowState(
            agent_outputs=[{"output": "data"}],
            errors=["Some warning"],
        )
        assert TaskRouter.should_continue(state) == "aggregate"

    def test_errors_without_outputs_routes_to_error(self) -> None:
        state = WorkflowState(
            agent_outputs=[],
            errors=["All agents failed"],
        )
        assert TaskRouter.should_continue(state) == "handle_error"
