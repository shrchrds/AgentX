"""Redis backend for the MemoryStore.

Stores memory records as JSON in Redis lists, keyed by agent and conversation.
Uses redis.asyncio for non-blocking I/O.
"""

from __future__ import annotations

import logging

from app.memory.store import MemoryStore
from app.models.memory import MemoryRecord

logger = logging.getLogger(__name__)


class RedisMemoryStore(MemoryStore):
    """Redis-backed implementation of MemoryStore.

    Records are stored as JSON strings in Redis lists with keys formatted as
    ``"agentx:{agent_id}:{conversation_id}"``.
    """

    def __init__(self, redis_url: str | None = None) -> None:
        self._client = None  # Lazy-initialized
        self._redis_url = redis_url

    async def _get_client(self):
        """Lazy-initialize the async Redis client."""
        if self._client is None:
            import redis.asyncio as aioredis

            if self._redis_url is None:
                from app.core.config import settings

                self._redis_url = settings.redis_url

            self._client = aioredis.from_url(
                self._redis_url,
                decode_responses=True,
            )
        return self._client

    @staticmethod
    def _key(agent_id: str, conversation_id: str) -> str:
        return f"agentx:{agent_id}:{conversation_id}"

    async def save_context(self, agent_id: str, conversation_id: str, data: dict) -> None:
        record = MemoryRecord(
            agent_id=agent_id,
            conversation_id=conversation_id,
            data=data,
        )
        client = await self._get_client()
        key = self._key(agent_id, conversation_id)
        await client.rpush(key, record.model_dump_json())

    async def load_context(self, agent_id: str, conversation_id: str) -> list[MemoryRecord]:
        client = await self._get_client()
        key = self._key(agent_id, conversation_id)
        raw_records = await client.lrange(key, 0, -1)
        records = [MemoryRecord.model_validate_json(r) for r in raw_records]
        return sorted(records, key=lambda r: r.timestamp)

    async def search(
        self, query: str, agent_id: str | None = None, top_k: int = 5
    ) -> list[MemoryRecord]:
        """Basic search: scans all keys matching pattern, filters by content.

        Note: This is a simple implementation. For production, consider
        using RediSearch or a dedicated vector search module.
        """
        client = await self._get_client()
        pattern = f"agentx:{agent_id}:*" if agent_id else "agentx:*"
        results: list[MemoryRecord] = []
        query_lower = query.lower()

        async for key in client.scan_iter(match=pattern):
            raw_records = await client.lrange(key, 0, -1)
            for raw in raw_records:
                record = MemoryRecord.model_validate_json(raw)
                data_str = " ".join(str(v) for v in record.data.values()).lower()
                if query_lower in data_str:
                    results.append(record)
                    if len(results) >= top_k:
                        return results

        return results

    async def clear(self, agent_id: str, conversation_id: str | None = None) -> None:
        client = await self._get_client()
        if conversation_id:
            key = self._key(agent_id, conversation_id)
            await client.delete(key)
        else:
            # Delete all keys for this agent
            pattern = f"agentx:{agent_id}:*"
            async for key in client.scan_iter(match=pattern):
                await client.delete(key)

    async def close(self) -> None:
        """Close the Redis connection."""
        if self._client:
            await self._client.aclose()
            self._client = None
