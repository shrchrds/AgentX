"""Agent Manager — registry and lifecycle management.

Handles agent registration, lookup, removal, and task-based routing.
Supports hot-plug: agents can be added/removed without downtime (FR4).
"""

from __future__ import annotations

import logging
import uuid

from app.agents.base import LegalAgent
from app.agents.case_analysis import CaseAnalysisAgent
from app.agents.contract_review import ContractReviewAgent
from app.agents.risk_analysis import RiskAnalysisAgent
from app.memory.store import MemoryStore
from app.models.agent import AgentInfo, AgentType

logger = logging.getLogger(__name__)

# Keyword mapping for task-based agent routing
_TASK_KEYWORDS: dict[AgentType, list[str]] = {
    AgentType.CONTRACT_REVIEW: ["contract", "clause", "agreement", "terms", "nda", "sla"],
    AgentType.CASE_ANALYSIS: ["case", "precedent", "ruling", "court", "judgment", "litigation"],
    AgentType.RISK_ANALYSIS: ["risk", "compliance", "regulatory", "liability", "exposure", "audit"],
}

# Agent type to class mapping
_AGENT_CLASSES: dict[AgentType, type[LegalAgent]] = {
    AgentType.CONTRACT_REVIEW: ContractReviewAgent,
    AgentType.CASE_ANALYSIS: CaseAnalysisAgent,
    AgentType.RISK_ANALYSIS: RiskAnalysisAgent,
}


class AgentManager:
    """Registry and lifecycle manager for specialized legal agents.

    On initialization, registers one default agent of each type.
    Supports hot-plug registration and removal at runtime.

    Args:
        memory_store: Shared memory backend for all agents.
        llm: Optional shared LLM instance (useful for testing with mocks).
    """

    def __init__(self, memory_store: MemoryStore, llm=None) -> None:
        self._registry: dict[str, LegalAgent] = {}
        self._memory_store = memory_store
        self._llm = llm
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register one default agent of each type."""
        for agent_type in AgentType:
            self.register_agent(agent_type)

    def register_agent(self, agent_type: AgentType, agent_id: str | None = None) -> AgentInfo:
        """Create and register a new agent.

        Args:
            agent_type: The specialization type.
            agent_id: Optional custom ID. Auto-generated if not provided.

        Returns:
            AgentInfo for the newly registered agent.

        Raises:
            ValueError: If the agent_type is not recognized.
            KeyError: If an agent with the same ID already exists.
        """
        if agent_type not in _AGENT_CLASSES:
            raise ValueError(f"Unknown agent type: {agent_type!r}")

        if agent_id is None:
            agent_id = f"{agent_type.value}-{uuid.uuid4().hex[:8]}"

        if agent_id in self._registry:
            raise KeyError(f"Agent already registered: {agent_id!r}")

        agent_cls = _AGENT_CLASSES[agent_type]
        agent = agent_cls(
            agent_id=agent_id,
            memory=self._memory_store,
            llm=self._llm,
        )
        self._registry[agent_id] = agent
        logger.info("Registered agent: %s (type=%s)", agent_id, agent_type.value)
        return agent.info

    def get_agent(self, agent_id: str) -> LegalAgent:
        """Retrieve a registered agent by ID.

        Args:
            agent_id: The agent's unique identifier.

        Returns:
            The LegalAgent instance.

        Raises:
            KeyError: If no agent with the given ID is registered.
        """
        if agent_id not in self._registry:
            raise KeyError(f"Agent not found: {agent_id!r}")
        return self._registry[agent_id]

    def list_agents(self) -> list[AgentInfo]:
        """List all registered agents.

        Returns:
            List of AgentInfo for all active agents.
        """
        return [agent.info for agent in self._registry.values()]

    def remove_agent(self, agent_id: str) -> None:
        """Deregister an agent (hot-plug removal).

        Args:
            agent_id: The agent to remove.

        Raises:
            KeyError: If no agent with the given ID is registered.
        """
        if agent_id not in self._registry:
            raise KeyError(f"Agent not found: {agent_id!r}")
        del self._registry[agent_id]
        logger.info("Removed agent: %s", agent_id)

    def get_agents_for_task(self, input_data: str) -> list[LegalAgent]:
        """Select the best agent(s) for a task based on content keywords.

        Scans the input text for domain-specific keywords and returns matching
        agents. If no keywords match, returns all agents for comprehensive analysis.

        Args:
            input_data: The task's input text.

        Returns:
            List of LegalAgent instances appropriate for the task.
        """
        input_lower = input_data.lower()
        matched_types: set[AgentType] = set()

        for agent_type, keywords in _TASK_KEYWORDS.items():
            if any(kw in input_lower for kw in keywords):
                matched_types.add(agent_type)

        if not matched_types:
            # No keyword match — use all agents for comprehensive analysis
            return list(self._registry.values())

        # Return all registered agents of the matched types
        return [agent for agent in self._registry.values() if agent.agent_type in matched_types]
