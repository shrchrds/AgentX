"""Agent-related data models.

Defines schemas for agent configuration, state, and response.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class AgentType(StrEnum):
    """Types of specialized legal agents available in the system."""

    CONTRACT_REVIEW = "contract_review"
    CASE_ANALYSIS = "case_analysis"
    RISK_ANALYSIS = "risk_analysis"


class AgentInfo(BaseModel):
    """Public metadata for a registered agent.

    Attributes:
        agent_id: Unique identifier for the agent instance.
        agent_type: The specialization type of the agent.
        description: Human-readable description of the agent's capabilities.
        status: Current operational status.
    """

    agent_id: str
    agent_type: AgentType
    description: str = ""
    status: str = "active"


class AgentState(BaseModel):
    """Internal state of an agent during task processing.

    Attributes:
        agent_id: The agent's identifier.
        context: Current context data for the ongoing task.
        history: List of previous interactions/messages.
        status: Processing status (pending, running, completed, failed).
    """

    agent_id: str
    context: dict = Field(default_factory=dict)
    history: list = Field(default_factory=list)
    status: str = "pending"


class AgentResponse(BaseModel):
    """Response produced by an agent after processing a task.

    Attributes:
        task_id: The task that was processed.
        agent_id: The agent that produced this response.
        output_data: The agent's analysis output.
        status: Processing result status.
        errors: Any errors encountered during processing.
    """

    task_id: str
    agent_id: str
    output_data: str = ""
    status: str = "completed"
    errors: list[str] = Field(default_factory=list)
