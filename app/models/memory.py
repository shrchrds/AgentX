"""Memory-related data models.

Defines the schema for memory records persisted by agents.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class MemoryRecord(BaseModel):
    """A single memory entry stored by an agent.

    Attributes:
        agent_id: The agent that owns this memory.
        conversation_id: Groups related memories within a task/session.
        data: Arbitrary structured data (e.g. messages, context snapshots).
        timestamp: When the memory was created (auto-set to UTC now).
    """

    agent_id: str
    conversation_id: str
    data: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
