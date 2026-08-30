"""Agent API routes.

GET /agents — list all registered agents
POST /agents — register a new agent
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.agents.manager import AgentManager
from app.api.dependencies import get_agent_manager
from app.core.security import get_api_key
from app.models.agent import AgentInfo, AgentType

logger = logging.getLogger(__name__)

router = APIRouter()


class RegisterAgentRequest(BaseModel):
    """Request body for registering a new agent."""

    agent_type: AgentType
    agent_id: str | None = None


@router.get(
    "/agents",
    response_model=list[AgentInfo],
    summary="List all registered agents",
    description="Returns metadata for all currently registered agents.",
)
async def list_agents(
    api_key: str = Depends(get_api_key),
    agent_manager: AgentManager = Depends(get_agent_manager),
) -> list[AgentInfo]:
    """List all registered agents."""
    return agent_manager.list_agents()


@router.post(
    "/agents",
    response_model=AgentInfo,
    status_code=status.HTTP_200_OK,
    summary="Register a new agent",
    description="Register a new specialized agent. Provide the agent type and "
    "optionally a custom agent ID.",
)
async def register_agent(
    request: RegisterAgentRequest,
    api_key: str = Depends(get_api_key),
    agent_manager: AgentManager = Depends(get_agent_manager),
) -> AgentInfo:
    """Register a new agent instance."""
    try:
        info = agent_manager.register_agent(
            agent_type=request.agent_type,
            agent_id=request.agent_id,
        )
        logger.info("Registered agent via API: %s", info.agent_id)
        return info
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
