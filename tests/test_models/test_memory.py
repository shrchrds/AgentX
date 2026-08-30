"""Tests for memory data models."""

from __future__ import annotations

from datetime import datetime, timezone

from app.models.memory import MemoryRecord


class TestMemoryRecord:
    """Tests for the MemoryRecord model."""

    def test_creation_with_auto_timestamp(self) -> None:
        record = MemoryRecord(
            agent_id="agent-1",
            conversation_id="conv-1",
            data={"message": "hello"},
        )
        assert record.agent_id == "agent-1"
        assert record.conversation_id == "conv-1"
        assert record.data == {"message": "hello"}
        assert record.timestamp is not None
        assert record.timestamp.tzinfo is not None

    def test_custom_timestamp(self) -> None:
        ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
        record = MemoryRecord(
            agent_id="agent-1",
            conversation_id="conv-1",
            data={},
            timestamp=ts,
        )
        assert record.timestamp == ts

    def test_default_data_is_empty_dict(self) -> None:
        record = MemoryRecord(
            agent_id="agent-1",
            conversation_id="conv-1",
        )
        assert record.data == {}

    def test_serialization_roundtrip(self) -> None:
        record = MemoryRecord(
            agent_id="agent-1",
            conversation_id="conv-1",
            data={"key": "value"},
        )
        data = record.model_dump()
        restored = MemoryRecord(**data)
        assert restored.agent_id == record.agent_id
        assert restored.data == record.data
