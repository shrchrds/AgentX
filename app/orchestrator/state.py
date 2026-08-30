"""Workflow state management for the orchestrator.

Defines the TypedDict state schema used by the LangGraph StateGraph,
plus helper functions for state initialization and completion checking.
"""

from __future__ import annotations

from typing import TypedDict

from app.models.task import TaskRequest, TaskStatus


class WorkflowState(TypedDict, total=False):
    """State flowing through the LangGraph orchestrator.

    Attributes:
        task_id: The task being processed.
        input_data: The original task input text.
        metadata: Task metadata from the request.
        target_agent_types: Agent types selected for this task.
        agent_outputs: Collected responses from agents.
        final_output: Aggregated result after all agents finish.
        status: Current task status.
        errors: Accumulated error messages.
        retry_count: Number of retries attempted.
    """

    task_id: str
    input_data: str
    metadata: dict
    target_agent_types: list[str]
    agent_outputs: list[dict]
    final_output: str
    status: str
    errors: list[str]
    retry_count: int


def initialize_state(task: TaskRequest) -> WorkflowState:
    """Create the initial workflow state from a task request.

    Args:
        task: The incoming task request.

    Returns:
        A fresh WorkflowState ready for the orchestrator.
    """
    return WorkflowState(
        task_id=task.task_id,
        input_data=task.input_data,
        metadata=task.metadata,
        target_agent_types=[],
        agent_outputs=[],
        final_output="",
        status=TaskStatus.PENDING,
        errors=[],
        retry_count=0,
    )


def is_complete(state: WorkflowState) -> bool:
    """Check if the workflow has reached a terminal state.

    Args:
        state: The current workflow state.

    Returns:
        True if status is COMPLETED or FAILED.
    """
    return state.get("status", "") in (TaskStatus.COMPLETED, TaskStatus.FAILED)
