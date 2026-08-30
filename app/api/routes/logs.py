"""Log API routes.

GET /logs/{task_id} — retrieve execution logs for a task
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_log_store
from app.core.security import get_api_key

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/logs/{task_id}",
    summary="Retrieve task execution logs",
    description="Returns structured execution log entries for a specific task.",
)
async def get_task_logs(
    task_id: str,
    api_key: str = Depends(get_api_key),
    log_store: dict = Depends(get_log_store),
) -> dict:
    """Retrieve execution logs for a task."""
    if task_id not in log_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No logs found for task: {task_id}",
        )
    return {"task_id": task_id, "logs": log_store[task_id]}
