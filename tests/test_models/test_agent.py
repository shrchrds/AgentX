"""Tests for agent data models."""

from __future__ import annotations

from app.models.agent import AgentInfo, AgentResponse, AgentState, AgentType


class TestAgentType:
    """Tests for the AgentType enum."""

    def test_enum_values(self) -> None:
        assert AgentType.CONTRACT_REVIEW == "contract_review"
        assert AgentType.CASE_ANALYSIS == "case_analysis"
        assert AgentType.RISK_ANALYSIS == "risk_analysis"

    def test_enum_has_three_members(self) -> None:
        assert len(AgentType) == 3


class TestAgentInfo:
    """Tests for the AgentInfo model."""

    def test_creation(self) -> None:
        info = AgentInfo(
            agent_id="agent-1",
            agent_type=AgentType.CONTRACT_REVIEW,
            description="Contract review agent",
        )
        assert info.agent_id == "agent-1"
        assert info.agent_type == AgentType.CONTRACT_REVIEW
        assert info.status == "active"

    def test_default_description(self) -> None:
        info = AgentInfo(agent_id="a", agent_type=AgentType.CASE_ANALYSIS)
        assert info.description == ""


class TestAgentState:
    """Tests for the AgentState model."""

    def test_defaults(self) -> None:
        state = AgentState(agent_id="agent-1")
        assert state.context == {}
        assert state.history == []
        assert state.status == "pending"

    def test_with_context(self) -> None:
        state = AgentState(
            agent_id="agent-1",
            context={"key": "value"},
            history=[{"role": "user", "content": "hi"}],
            status="running",
        )
        assert state.context["key"] == "value"
        assert len(state.history) == 1
        assert state.status == "running"


class TestAgentResponse:
    """Tests for the AgentResponse model."""

    def test_creation(self) -> None:
        resp = AgentResponse(
            task_id="task-1",
            agent_id="agent-1",
            output_data="Analysis result",
        )
        assert resp.task_id == "task-1"
        assert resp.agent_id == "agent-1"
        assert resp.status == "completed"
        assert resp.errors == []

    def test_with_errors(self) -> None:
        resp = AgentResponse(
            task_id="task-1",
            agent_id="agent-1",
            output_data="",
            status="failed",
            errors=["LLM timeout"],
        )
        assert resp.status == "failed"
        assert len(resp.errors) == 1
