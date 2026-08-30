"""Abstract memory store interface.

Defines the contract all memory backends must implement, plus a factory
function to instantiate the configured backend.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.memory import MemoryRecord


class MemoryStore(ABC):
    """Abstract base class for agent memory persistence.

    All methods are async to support both in-memory and networked backends
    (e.g. Redis) uniformly.
    """

    @abstractmethod
    async def save_context(self, agent_id: str, conversation_id: str, data: dict) -> None:
        """Persist a context snapshot for an agent conversation.

        Args:
            agent_id: The agent that owns this memory.
            conversation_id: Groups related memories within a session.
            data: Arbitrary structured data to persist.
        """

    @abstractmethod
    async def load_context(self, agent_id: str, conversation_id: str) -> list[MemoryRecord]:
        """Load all memory records for an agent conversation.

        Args:
            agent_id: The agent whose memories to load.
            conversation_id: The conversation/session to load.

        Returns:
            List of MemoryRecord entries, ordered by timestamp.
        """

    @abstractmethod
    async def search(
        self, query: str, agent_id: str | None = None, top_k: int = 5
    ) -> list[MemoryRecord]:
        """Search memories by content similarity or keyword matching.

        Args:
            query: The search query string.
            agent_id: Optional filter to a specific agent's memories.
            top_k: Maximum number of results to return.

        Returns:
            List of matching MemoryRecord entries.
        """

    @abstractmethod
    async def clear(self, agent_id: str, conversation_id: str | None = None) -> None:
        """Delete memory records.

        Args:
            agent_id: The agent whose memories to clear.
            conversation_id: If provided, clear only this conversation.
                If None, clear all memories for the agent.
        """


def create_memory_store(backend: str) -> MemoryStore:
    """Factory function to instantiate the configured memory backend.

    Args:
        backend: One of "memory", "faiss", or "redis".

    Returns:
        A MemoryStore implementation.

    Raises:
        ValueError: If the backend name is not recognized.
    """
    if backend == "memory":
        from app.memory.backends.in_memory import InMemoryStore

        return InMemoryStore()
    elif backend == "faiss":
        from app.memory.backends.faiss_backend import FAISSMemoryStore

        return FAISSMemoryStore()
    elif backend == "redis":
        from app.memory.backends.redis_backend import RedisMemoryStore

        return RedisMemoryStore()
    else:
        raise ValueError(
            f"Unknown memory backend: {backend!r}. " f"Valid options: 'memory', 'faiss', 'redis'."
        )
