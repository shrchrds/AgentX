"""Tests for the Redis memory store backend.

Redis client is fully mocked — no live Redis instance required.
"""

from __future__ import annotations

import pytest

from app.memory.backends.redis_backend import RedisMemoryStore


class FakeRedis:
    """Minimal async Redis mock using in-memory dicts and lists."""

    def __init__(self) -> None:
        self._data: dict[str, list[str]] = {}

    async def rpush(self, key: str, value: str) -> None:
        if key not in self._data:
            self._data[key] = []
        self._data[key].append(value)

    async def lrange(self, key: str, start: int, end: int) -> list[str]:
        return self._data.get(key, [])[:]

    async def delete(self, key: str) -> None:
        self._data.pop(key, None)

    async def scan_iter(self, match: str = "*"):
        """Yield keys matching a simple glob pattern."""
        import fnmatch

        for key in list(self._data.keys()):
            if fnmatch.fnmatch(key, match):
                yield key

    async def aclose(self) -> None:
        self._data.clear()


@pytest.fixture
def store() -> RedisMemoryStore:
    """Create a Redis store with a fake client."""
    s = RedisMemoryStore(redis_url="redis://fake:6379/0")
    s._client = FakeRedis()
    return s


class TestRedisMemoryStore:
    """Tests for the Redis backend with mocked client."""

    async def test_save_and_load(self, store: RedisMemoryStore) -> None:
        await store.save_context("agent-1", "conv-1", {"message": "hello"})
        records = await store.load_context("agent-1", "conv-1")
        assert len(records) == 1
        assert records[0].data == {"message": "hello"}

    async def test_multiple_saves(self, store: RedisMemoryStore) -> None:
        await store.save_context("agent-1", "conv-1", {"msg": "first"})
        await store.save_context("agent-1", "conv-1", {"msg": "second"})
        records = await store.load_context("agent-1", "conv-1")
        assert len(records) == 2

    async def test_load_empty(self, store: RedisMemoryStore) -> None:
        records = await store.load_context("agent-1", "nonexistent")
        assert records == []

    async def test_clear_specific_conversation(self, store: RedisMemoryStore) -> None:
        await store.save_context("agent-1", "conv-1", {"msg": "keep"})
        await store.save_context("agent-1", "conv-2", {"msg": "delete"})
        await store.clear("agent-1", "conv-2")
        r1 = await store.load_context("agent-1", "conv-1")
        r2 = await store.load_context("agent-1", "conv-2")
        assert len(r1) == 1
        assert len(r2) == 0

    async def test_clear_all_for_agent(self, store: RedisMemoryStore) -> None:
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

    async def test_search_finds_matching(self, store: RedisMemoryStore) -> None:
        await store.save_context("agent-1", "conv-1", {"content": "contract review"})
        await store.save_context("agent-1", "conv-1", {"content": "case analysis"})
        results = await store.search("contract")
        assert len(results) == 1
        assert "contract" in results[0].data["content"]

    async def test_search_with_agent_filter(self, store: RedisMemoryStore) -> None:
        await store.save_context("agent-1", "conv-1", {"content": "hello from 1"})
        await store.save_context("agent-2", "conv-1", {"content": "hello from 2"})
        results = await store.search("hello", agent_id="agent-1")
        assert len(results) == 1
        assert results[0].agent_id == "agent-1"

    async def test_close(self, store: RedisMemoryStore) -> None:
        await store.close()
        assert store._client is None
