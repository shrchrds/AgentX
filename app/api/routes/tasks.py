"""Task API routes.

POST /tasks — submit a new legal task
GET /tasks/{task_id} — get task status and result
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_log_store, get_orchestrator, get_task_store
from app.core.security import get_api_key
from app.models.task import TaskRequest, TaskResponse
from app.orchestrator.graph import AgentOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit a new legal task",
    description="Submit a legal task for multi-agent analysis. The task is processed "
    "by the orchestrator which routes it to appropriate specialized agents.",
)
async def create_task(
    task_request: TaskRequest,
    api_key: str = Depends(get_api_key),
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    task_store: dict = Depends(get_task_store),
    log_store: dict = Depends(get_log_store),
) -> TaskResponse:
    """Submit and process a legal task."""
    logger.info("Received task: %s", task_request.task_id)

    # Log task submission
    if task_request.task_id not in log_store:
        log_store[task_request.task_id] = []
    log_store[task_request.task_id].append(
        {
            "event": "task_submitted",
            "task_id": task_request.task_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

    # Run the orchestrator workflow
    result = await orchestrator.run_workflow(task_request)

    # Store the result
    task_store[task_request.task_id] = result

    # Log completion
    log_store[task_request.task_id].append(
        {
            "event": "task_completed",
            "task_id": task_request.task_id,
            "status": result.status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )

    return result


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Get task status and result",
    description="Retrieve the status and result of a previously submitted task.",
)
async def get_task(
    task_id: str,
    api_key: str = Depends(get_api_key),
    task_store: dict = Depends(get_task_store),
) -> TaskResponse:
    """Retrieve task status and result by ID."""
    if task_id not in task_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {task_id}",
        )
    return task_store[task_id]
