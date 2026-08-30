"""FastAPI application entrypoint for AgentX.

Initializes the app, memory store, agent manager, and orchestrator on startup.
Includes all API route routers under /api/v1.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.agents.manager import AgentManager
from app.api.routes import agents, logs, tasks
from app.core.config import settings
from app.core.logging import setup_logging
from app.memory.store import create_memory_store
from app.orchestrator.graph import AgentOrchestrator

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler — initialize and tear down resources."""
    # --- Startup ---
    setup_logging(settings.log_level)
    logger.info("Starting AgentX application")

    # Initialize memory store
    memory_store = create_memory_store(settings.memory_backend)
    app.state.memory_store = memory_store

    # Initialize agent manager (auto-registers default agents)
    agent_manager = AgentManager(memory_store=memory_store)
    app.state.agent_manager = agent_manager

    # Initialize orchestrator
    orchestrator = AgentOrchestrator(agent_manager=agent_manager)
    app.state.orchestrator = orchestrator

    # In-memory task store for tracking task results
    app.state.task_store: dict = {}

    # In-memory log store for task execution logs
    app.state.log_store: dict[str, list[dict]] = {}

    logger.info("AgentX started successfully")
    yield

    # --- Shutdown ---
    logger.info("Shutting down AgentX")


app = FastAPI(
    title="AgentX",
    description=(
        "Multi-Agent Collaboration Framework for Legal Domain Tasks. "
        "Orchestrates specialized AI agents that collaboratively solve "
        "legal domain problems via dynamic, context-aware workflows."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tasks.router, prefix="/api/v1", tags=["Tasks"])
app.include_router(agents.router, prefix="/api/v1", tags=["Agents"])
app.include_router(logs.router, prefix="/api/v1", tags=["Logs"])


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch unhandled exceptions and return a generic 500 error.

    Never exposes internal exception details to the client.
    """
    logger.error("Unhandled exception: %s", type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."},
    )


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}
