"""In-memory backend for the MemoryStore.

Simple dict-based storage suitable for development and testing.
Thread-safe via asyncio.Lock.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict

from app.memory.store import MemoryStore
from app.models.memory import MemoryRecord


class InMemoryStore(MemoryStore):
    """Dict-backed in-memory implementation of MemoryStore.

    Keys are formatted as ``"{agent_id}:{conversation_id}"``.
    All operations are guarded by an asyncio Lock for safety.
    """

    def __init__(self) -> None:
        self._store: dict[str, list[MemoryRecord]] = defaultdict(list)
        self._lock = asyncio.Lock()

    @staticmethod
    def _key(agent_id: str, conversation_id: str) -> str:
        return f"{agent_id}:{conversation_id}"

    async def save_context(self, agent_id: str, conversation_id: str, data: dict) -> None:
        record = MemoryRecord(
            agent_id=agent_id,
            conversation_id=conversation_id,
            data=data,
        )
        async with self._lock:
            self._store[self._key(agent_id, conversation_id)].append(record)

    async def load_context(self, agent_id: str, conversation_id: str) -> list[MemoryRecord]:
        async with self._lock:
            records = self._store.get(self._key(agent_id, conversation_id), [])
            return sorted(records, key=lambda r: r.timestamp)

    async def search(
        self, query: str, agent_id: str | None = None, top_k: int = 5
    ) -> list[MemoryRecord]:
        """Simple substring search across all stored data values."""
        results: list[MemoryRecord] = []
        query_lower = query.lower()
        async with self._lock:
            for key, records in self._store.items():
                for record in records:
                    if agent_id and record.agent_id != agent_id:
                        continue
                    # Search in string representations of data values
                    data_str = " ".join(str(v) for v in record.data.values()).lower()
                    if query_lower in data_str:
                        results.append(record)
                        if len(results) >= top_k:
                            return results
        return results

    async def clear(self, agent_id: str, conversation_id: str | None = None) -> None:
        async with self._lock:
            if conversation_id:
                key = self._key(agent_id, conversation_id)
                self._store.pop(key, None)
            else:
                # Clear all conversations for this agent
                keys_to_remove = [k for k in self._store if k.startswith(f"{agent_id}:")]
                for k in keys_to_remove:
                    del self._store[k]
