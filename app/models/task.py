"""Task-related data models.

Defines request/response schemas for legal task submission and status tracking.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Annotated

from pydantic import AliasChoices, BaseModel, BeforeValidator, Field, field_validator

from app.core.security import sanitize_input


def _sanitize_str(v: str) -> str:
    """Pre-validation sanitizer for input_data."""
    if isinstance(v, str):
        return sanitize_input(v)
    return v


class TaskStatus(StrEnum):
    """Possible states of a task throughout its lifecycle."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# Sanitize before Pydantic's max_length constraint fires
SanitizedStr = Annotated[str, BeforeValidator(_sanitize_str)]


class TaskRequest(BaseModel):
    """Schema for submitting a new legal task.

    Attributes:
        task_id: Unique identifier. Auto-generated if not provided.
        input_data: The legal query or document to process (max 50,000 chars).
        metadata: Optional context for the task.
    """

    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    input_data: SanitizedStr = Field(
        ...,
        min_length=1,
        max_length=50_000,
        validation_alias=AliasChoices("input_data", "input"),
    )
    metadata: dict = Field(default_factory=dict)

    @field_validator("task_id")
    @classmethod
    def task_id_must_not_be_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("task_id must not be empty")
        return v


class TaskResponse(BaseModel):
    """Schema for task status and results.

    Attributes:
        task_id: The unique task identifier.
        status: Current status of the task.
        output_data: The final output after processing (None while pending/running).
        errors: List of error messages if the task failed.
        created_at: Timestamp when the task was submitted.
        completed_at: Timestamp when the task finished (None if not yet complete).
    """

    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    output_data: str | None = None
    errors: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None


class DocumentExtractResponse(BaseModel):
    """Schema for document text extraction responses."""

    filename: str
    content: str
    char_count: int
    format: str
    truncated: bool = False
    metadata: dict = Field(default_factory=dict)
