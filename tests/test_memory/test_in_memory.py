"""Tests for the InMemoryStore backend."""

from __future__ import annotations

import pytest

from app.memory.backends.in_memory import InMemoryStore


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


class TestInMemoryStore:
    """Tests for the in-memory backend."""

    async def test_save_and_load(self, store: InMemoryStore) -> None:
        await store.save_context("agent-1", "conv-1", {"message": "hello"})
        records = await store.load_context("agent-1", "conv-1")
        assert len(records) == 1
        assert records[0].data == {"message": "hello"}
        assert records[0].agent_id == "agent-1"
        assert records[0].conversation_id == "conv-1"

    async def test_multiple_saves(self, store: InMemoryStore) -> None:
        await store.save_context("agent-1", "conv-1", {"msg": "first"})
        await store.save_context("agent-1", "conv-1", {"msg": "second"})
        records = await store.load_context("agent-1", "conv-1")
        assert len(records) == 2

    async def test_load_empty(self, store: InMemoryStore) -> None:
        records = await store.load_context("agent-1", "conv-1")
        assert records == []

    async def test_isolation_between_agents(self, store: InMemoryStore) -> None:
        await store.save_context("agent-1", "conv-1", {"msg": "a1"})
        await store.save_context("agent-2", "conv-1", {"msg": "a2"})
        r1 = await store.load_context("agent-1", "conv-1")
        r2 = await store.load_context("agent-2", "conv-1")
        assert len(r1) == 1
        assert len(r2) == 1
        assert r1[0].data["msg"] == "a1"
        assert r2[0].data["msg"] == "a2"

    async def test_isolation_between_conversations(self, store: InMemoryStore) -> None:
        await store.save_context("agent-1", "conv-1", {"msg": "c1"})
        await store.save_context("agent-1", "conv-2", {"msg": "c2"})
        r1 = await store.load_context("agent-1", "conv-1")
        r2 = await store.load_context("agent-1", "conv-2")
        assert len(r1) == 1
        assert len(r2) == 1

    async def test_search_finds_matching(self, store: InMemoryStore) -> None:
        await store.save_context("agent-1", "conv-1", {"content": "contract review needed"})
        await store.save_context("agent-1", "conv-1", {"content": "case analysis done"})
        results = await store.search("contract")
        assert len(results) == 1
        assert "contract" in results[0].data["content"]

    async def test_search_with_agent_filter(self, store: InMemoryStore) -> None:
        await store.save_context("agent-1", "conv-1", {"content": "hello world"})
        await store.save_context("agent-2", "conv-1", {"content": "hello there"})
        results = await store.search("hello", agent_id="agent-1")
        assert len(results) == 1
        assert results[0].agent_id == "agent-1"

    async def test_search_respects_top_k(self, store: InMemoryStore) -> None:
        for i in range(10):
            await store.save_context("agent-1", "conv-1", {"content": f"item {i}"})
        results = await store.search("item", top_k=3)
        assert len(results) == 3

    async def test_clear_specific_conversation(self, store: InMemoryStore) -> None:
        await store.save_context("agent-1", "conv-1", {"msg": "keep"})
        await store.save_context("agent-1", "conv-2", {"msg": "delete"})
        await store.clear("agent-1", "conv-2")
        r1 = await store.load_context("agent-1", "conv-1")
        r2 = await store.load_context("agent-1", "conv-2")
        assert len(r1) == 1
        assert len(r2) == 0

    async def test_clear_all_for_agent(self, store: InMemoryStore) -> None:
        await store.save_context("agent-1", "conv-1", {"msg": "a"})
        await store.save_context("agent-1", "conv-2", {"msg": "b"})
        await store.save_context("agent-2", "conv-1", {"msg": "c"})
        await store.clear("agent-1")
        r1 = await store.load_context("agent-1", "conv-1")
        r2 = await store.load_context("agent-1", "conv-2")
        r3 = await store.load_context("agent-2", "conv-1")
        assert len(r1) == 0
        assert len(r2) == 0
        assert len(r3) == 1
