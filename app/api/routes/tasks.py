"""Task API routes.

POST /tasks — submit a new legal task
GET /tasks/{task_id} — get task status and result
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.dependencies import get_log_store, get_orchestrator, get_task_store
from app.core.security import get_api_key
from app.models.task import DocumentExtractResponse, TaskRequest, TaskResponse
from app.orchestrator.graph import AgentOrchestrator
from app.utils.document_parser import DocumentParsingError, extract_document_text

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
    "/tasks",
    response_model=list[TaskResponse],
    summary="List all legal tasks",
    description="Retrieve all submitted tasks and their status/results.",
)
async def list_tasks(
    api_key: str = Depends(get_api_key),
    task_store: dict = Depends(get_task_store),
) -> list[TaskResponse]:
    """List all submitted tasks in reverse chronological order."""
    return list(task_store.values())[::-1]


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


@router.post(
    "/tasks/extract-text",
    response_model=DocumentExtractResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract text from uploaded legal document",
    description="Extracts raw text and metadata from PDF (.pdf), Word (.docx), "
    "or text/markdown (.txt, .md) files for review prior to running analysis.",
)
async def extract_document_route(
    file: UploadFile = File(...),
    api_key: str = Depends(get_api_key),
) -> DocumentExtractResponse:
    """Parse and extract text from an uploaded legal document."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename must not be empty.",
        )

    try:
        content_bytes = await file.read()
        extracted = extract_document_text(file.filename, content_bytes)
        return DocumentExtractResponse(
            filename=extracted.filename,
            content=extracted.content,
            char_count=extracted.char_count,
            format=extracted.format,
            truncated=extracted.truncated,
            metadata=extracted.metadata,
        )
    except DocumentParsingError as exc:
        logger.warning("Document parsing failed for %s: %s", file.filename, exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/tasks/upload",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit a legal document directly for multi-agent review",
    description="Directly uploads a PDF, DOCX, or TXT document, extracts its content, "
    "and immediately triggers multi-agent orchestration.",
)
async def upload_document_task(
    file: UploadFile = File(...),
    task_id: str | None = Form(None),
    metadata: str | None = Form(None),
    api_key: str = Depends(get_api_key),
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    task_store: dict = Depends(get_task_store),
    log_store: dict = Depends(get_log_store),
) -> TaskResponse:
    """Upload document file and execute multi-agent task immediately."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename must not be empty.",
        )

    try:
        content_bytes = await file.read()
        extracted = extract_document_text(file.filename, content_bytes)
    except DocumentParsingError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    parsed_metadata = {}
    if metadata:
        try:
            parsed_metadata = json.loads(metadata)
        except json.JSONDecodeError:
            parsed_metadata = {"raw_metadata": metadata}

    parsed_metadata.update(
        {
            "source_file": extracted.filename,
            "document_format": extracted.format,
            "document_char_count": extracted.char_count,
            **extracted.metadata,
        }
    )

    req_kwargs: dict = {
        "input_data": extracted.content,
        "metadata": parsed_metadata,
    }
    if task_id and task_id.strip():
        req_kwargs["task_id"] = task_id.strip()

    task_request = TaskRequest(**req_kwargs)
    return await create_task(
        task_request=task_request,
        api_key=api_key,
        orchestrator=orchestrator,
        task_store=task_store,
        log_store=log_store,
    )
