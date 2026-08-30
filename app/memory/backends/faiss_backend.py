"""FAISS vector store backend for the MemoryStore.

Uses OpenAI embeddings for vectorization and FAISS for similarity search.
Embeddings are initialized lazily on first use.
"""

from __future__ import annotations

import asyncio
import logging

import numpy as np

from app.memory.store import MemoryStore
from app.models.memory import MemoryRecord

logger = logging.getLogger(__name__)


class FAISSMemoryStore(MemoryStore):
    """FAISS-backed memory store with OpenAI embedding support.

    Vectors are stored in a flat L2 index. Metadata is kept in a parallel list.
    Embeddings model is initialized lazily to avoid import-time API calls.
    """

    def __init__(self) -> None:
        self._records: list[MemoryRecord] = []
        self._index = None  # Lazy-initialized faiss.IndexFlatL2
        self._embeddings = None  # Lazy-initialized OpenAIEmbeddings
        self._lock = asyncio.Lock()
        self._dimension: int | None = None

    def _get_embeddings(self):
        """Lazy-initialize the OpenAI embeddings model."""
        if self._embeddings is None:
            from langchain_openai import OpenAIEmbeddings

            from app.core.config import settings

            self._embeddings = OpenAIEmbeddings(
                openai_api_key=settings.openai_api_key,
            )
        return self._embeddings

    def _get_index(self, dimension: int):
        """Lazy-initialize the FAISS index with the given dimension."""
        if self._index is None:
            import faiss

            self._dimension = dimension
            self._index = faiss.IndexFlatL2(dimension)
        return self._index

    def _text_from_data(self, data: dict) -> str:
        """Extract a searchable text string from a data dict."""
        return " ".join(str(v) for v in data.values())

    async def save_context(self, agent_id: str, conversation_id: str, data: dict) -> None:
        record = MemoryRecord(
            agent_id=agent_id,
            conversation_id=conversation_id,
            data=data,
        )
        text = self._text_from_data(data)

        async with self._lock:
            embeddings = self._get_embeddings()
            # Run embedding in executor to avoid blocking
            loop = asyncio.get_event_loop()
            vector = await loop.run_in_executor(None, lambda: embeddings.embed_query(text))
            vector_np = np.array([vector], dtype=np.float32)

            index = self._get_index(len(vector))
            index.add(vector_np)
            self._records.append(record)

    async def load_context(self, agent_id: str, conversation_id: str) -> list[MemoryRecord]:
        async with self._lock:
            results = [
                r
                for r in self._records
                if r.agent_id == agent_id and r.conversation_id == conversation_id
            ]
            return sorted(results, key=lambda r: r.timestamp)

    async def search(
        self, query: str, agent_id: str | None = None, top_k: int = 5
    ) -> list[MemoryRecord]:
        async with self._lock:
            if not self._records or self._index is None:
                return []

            embeddings = self._get_embeddings()
            loop = asyncio.get_event_loop()
            query_vector = await loop.run_in_executor(None, lambda: embeddings.embed_query(query))
            query_np = np.array([query_vector], dtype=np.float32)

            # Search for more than top_k in case we need to filter by agent_id
            search_k = min(top_k * 3, len(self._records))
            distances, indices = self._index.search(query_np, search_k)

            results: list[MemoryRecord] = []
            for idx in indices[0]:
                if idx < 0 or idx >= len(self._records):
                    continue
                record = self._records[idx]
                if agent_id and record.agent_id != agent_id:
                    continue
                results.append(record)
                if len(results) >= top_k:
                    break

            return results

    async def clear(self, agent_id: str, conversation_id: str | None = None) -> None:
        async with self._lock:
            if conversation_id:
                self._records = [
                    r
                    for r in self._records
                    if not (r.agent_id == agent_id and r.conversation_id == conversation_id)
                ]
            else:
                self._records = [r for r in self._records if r.agent_id != agent_id]

            # Rebuild the FAISS index from remaining records
            if self._records and self._dimension:
                import faiss

                self._index = faiss.IndexFlatL2(self._dimension)
                embeddings = self._get_embeddings()
                texts = [self._text_from_data(r.data) for r in self._records]
                loop = asyncio.get_event_loop()
                vectors = await loop.run_in_executor(
                    None, lambda: embeddings.embed_documents(texts)
                )
                vectors_np = np.array(vectors, dtype=np.float32)
                self._index.add(vectors_np)
            else:
                self._index = None
                self._dimension = None
