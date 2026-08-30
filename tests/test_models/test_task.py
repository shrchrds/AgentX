"""Tests for task data models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models.task import TaskRequest, TaskResponse, TaskStatus


class TestTaskStatus:
    """Tests for the TaskStatus enum."""

    def test_enum_values(self) -> None:
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.RUNNING == "running"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"

    def test_enum_has_four_members(self) -> None:
        assert len(TaskStatus) == 4


class TestTaskRequest:
    """Tests for the TaskRequest model."""

    def test_valid_creation(self) -> None:
        req = TaskRequest(input_data="Review this contract for risks.")
        assert req.input_data == "Review this contract for risks."
        assert req.task_id  # auto-generated UUID
        assert req.metadata == {}

    def test_custom_task_id(self) -> None:
        req = TaskRequest(task_id="custom-123", input_data="Test input")
        assert req.task_id == "custom-123"

    def test_empty_task_id_rejected(self) -> None:
        with pytest.raises(ValidationError, match="task_id must not be empty"):
            TaskRequest(task_id="   ", input_data="Test input")

    def test_empty_input_data_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TaskRequest(input_data="")

    def test_oversized_input_data_truncated(self) -> None:
        long_input = "a" * 60_000
        req = TaskRequest(input_data=long_input)
        assert len(req.input_data) <= 50_000

    def test_control_characters_stripped(self) -> None:
        req = TaskRequest(input_data="hello\x00world\x01test")
        assert "\x00" not in req.input_data
        assert "\x01" not in req.input_data

    def test_metadata_default(self) -> None:
        req = TaskRequest(input_data="Test")
        assert req.metadata == {}

    def test_metadata_with_values(self) -> None:
        req = TaskRequest(input_data="Test", metadata={"source": "api"})
        assert req.metadata == {"source": "api"}


class TestTaskResponse:
    """Tests for the TaskResponse model."""

    def test_default_status_is_pending(self) -> None:
        resp = TaskResponse(task_id="test-1")
        assert resp.status == TaskStatus.PENDING
        assert resp.output_data is None
        assert resp.errors == []
        assert resp.completed_at is None

    def test_created_at_auto_set(self) -> None:
        resp = TaskResponse(task_id="test-1")
        assert resp.created_at is not None

    def test_serialization_roundtrip(self) -> None:
        resp = TaskResponse(
            task_id="test-1",
            status=TaskStatus.COMPLETED,
            output_data="Analysis complete.",
        )
        data = resp.model_dump()
        restored = TaskResponse(**data)
        assert restored.task_id == resp.task_id
        assert restored.status == TaskStatus.COMPLETED
        assert restored.output_data == "Analysis complete."
