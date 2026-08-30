"""Tests for workflow state management."""

from __future__ import annotations

from app.models.task import TaskRequest, TaskStatus
from app.orchestrator.state import WorkflowState, initialize_state, is_complete


class TestWorkflowState:
    """Tests for state initialization and completion checking."""

    def test_initialize_state(self) -> None:
        task = TaskRequest(task_id="t-1", input_data="Review contract.")
        state = initialize_state(task)
        assert state["task_id"] == "t-1"
        assert state["input_data"] == "Review contract."
        assert state["status"] == TaskStatus.PENDING
        assert state["agent_outputs"] == []
        assert state["errors"] == []
        assert state["retry_count"] == 0

    def test_is_complete_pending(self) -> None:
        state = WorkflowState(status=TaskStatus.PENDING)
        assert is_complete(state) is False

    def test_is_complete_running(self) -> None:
        state = WorkflowState(status=TaskStatus.RUNNING)
        assert is_complete(state) is False

    def test_is_complete_completed(self) -> None:
        state = WorkflowState(status=TaskStatus.COMPLETED)
        assert is_complete(state) is True

    def test_is_complete_failed(self) -> None:
        state = WorkflowState(status=TaskStatus.FAILED)
        assert is_complete(state) is True

    def test_is_complete_empty_state(self) -> None:
        state = WorkflowState()
        assert is_complete(state) is False
