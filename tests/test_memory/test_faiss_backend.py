"""Tests for the FAISS memory store backend.

All OpenAI embedding calls are mocked to return deterministic vectors.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.memory.backends.faiss_backend import FAISSMemoryStore


def _mock_embed_query(text: str) -> list[float]:
    """Return a deterministic 4-dim vector based on text hash."""
    h = hash(text) % 10000
    return [float(h % 10), float((h // 10) % 10), float((h // 100) % 10), float((h // 1000) % 10)]


def _mock_embed_documents(texts: list[str]) -> list[list[float]]:
    """Return deterministic vectors for a batch of texts."""
    return [_mock_embed_query(t) for t in texts]


@pytest.fixture
def store() -> FAISSMemoryStore:
    """Create a FAISS store with mocked embeddings."""
    s = FAISSMemoryStore()
    mock_embeddings = MagicMock()
    mock_embeddings.embed_query = _mock_embed_query
    mock_embeddings.embed_documents = _mock_embed_documents
    s._embeddings = mock_embeddings
    return s


class TestFAISSMemoryStore:
    """Tests for the FAISS backend with mocked embeddings."""

    async def test_save_and_load(self, store: FAISSMemoryStore) -> None:
        await store.save_context("agent-1", "conv-1", {"content": "test data"})
        records = await store.load_context("agent-1", "conv-1")
        assert len(records) == 1
        assert records[0].data["content"] == "test data"

    async def test_search_returns_results(self, store: FAISSMemoryStore) -> None:
        await store.save_context("agent-1", "conv-1", {"content": "contract review"})
        await store.save_context("agent-1", "conv-1", {"content": "case analysis"})
        results = await store.search("contract")
        assert len(results) > 0

    async def test_search_respects_top_k(self, store: FAISSMemoryStore) -> None:
        for i in range(10):
            await store.save_context("agent-1", "conv-1", {"content": f"document {i}"})
        results = await store.search("document", top_k=3)
        assert len(results) <= 3

    async def test_search_empty_store(self, store: FAISSMemoryStore) -> None:
        results = await store.search("anything")
        assert results == []

    async def test_search_with_agent_filter(self, store: FAISSMemoryStore) -> None:
        await store.save_context("agent-1", "conv-1", {"content": "hello from agent 1"})
        await store.save_context("agent-2", "conv-1", {"content": "hello from agent 2"})
        results = await store.search("hello", agent_id="agent-1", top_k=10)
        assert all(r.agent_id == "agent-1" for r in results)

    async def test_clear_specific_conversation(self, store: FAISSMemoryStore) -> None:
        await store.save_context("agent-1", "conv-1", {"content": "keep"})
        await store.save_context("agent-1", "conv-2", {"content": "remove"})
        await store.clear("agent-1", "conv-2")
        r1 = await store.load_context("agent-1", "conv-1")
        r2 = await store.load_context("agent-1", "conv-2")
        assert len(r1) == 1
        assert len(r2) == 0

    async def test_clear_all_for_agent(self, store: FAISSMemoryStore) -> None:
        await store.save_context("agent-1", "conv-1", {"content": "a"})
        await store.save_context("agent-1", "conv-2", {"content": "b"})
        await store.clear("agent-1")
        r1 = await store.load_context("agent-1", "conv-1")
        r2 = await store.load_context("agent-1", "conv-2")
        assert len(r1) == 0
        assert len(r2) == 0
