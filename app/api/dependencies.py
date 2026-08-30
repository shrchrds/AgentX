"""Shared FastAPI dependencies.

Provides dependency injection for auth, rate limiting, orchestrator, and agent manager.
"""

from __future__ import annotations

from fastapi import Request

from app.agents.manager import AgentManager
from app.orchestrator.graph import AgentOrchestrator


async def get_orchestrator(request: Request) -> AgentOrchestrator:
    """Retrieve the orchestrator from application state.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The shared AgentOrchestrator instance.
    """
    return request.app.state.orchestrator


async def get_agent_manager(request: Request) -> AgentManager:
    """Retrieve the agent manager from application state.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The shared AgentManager instance.
    """
    return request.app.state.agent_manager


async def get_task_store(request: Request) -> dict:
    """Retrieve the in-memory task store from application state."""
    return request.app.state.task_store


async def get_log_store(request: Request) -> dict:
    """Retrieve the in-memory log store from application state."""
    return request.app.state.log_store
