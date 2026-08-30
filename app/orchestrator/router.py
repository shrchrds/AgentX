"""Task routing logic for the orchestrator.

Classifies tasks to determine which agent types should handle them,
using keyword matching with optional LLM fallback.
"""

from __future__ import annotations

import logging

from app.models.agent import AgentType
from app.orchestrator.state import WorkflowState

logger = logging.getLogger(__name__)

# Keyword → agent type mapping
_TASK_KEYWORDS: dict[AgentType, list[str]] = {
    AgentType.CONTRACT_REVIEW: [
        "contract",
        "clause",
        "agreement",
        "terms",
        "nda",
        "sla",
        "warranty",
    ],
    AgentType.CASE_ANALYSIS: [
        "case",
        "precedent",
        "ruling",
        "court",
        "judgment",
        "litigation",
        "appeal",
    ],
    AgentType.RISK_ANALYSIS: [
        "risk",
        "compliance",
        "regulatory",
        "liability",
        "exposure",
        "audit",
        "penalty",
    ],
}


class TaskRouter:
    """Routes tasks to appropriate agent types based on content analysis."""

    @staticmethod
    def classify_task(input_data: str, metadata: dict | None = None) -> list[AgentType]:
        """Determine which agent types should process this task.

        Uses keyword matching to identify relevant agent specializations.
        If no keywords match, returns all types for comprehensive analysis.

        Args:
            input_data: The task input text.
            metadata: Optional metadata that may contain routing hints.

        Returns:
            List of AgentType values appropriate for this task.
        """
        # Check metadata for explicit routing hints
        if metadata and "agent_type" in metadata:
            try:
                return [AgentType(metadata["agent_type"])]
            except ValueError:
                pass  # Invalid type in metadata, fall through to keyword matching

        input_lower = input_data.lower()
        matched: list[AgentType] = []

        for agent_type, keywords in _TASK_KEYWORDS.items():
            if any(kw in input_lower for kw in keywords):
                matched.append(agent_type)

        if not matched:
            logger.info("No keyword match for task, routing to all agents")
            return list(AgentType)

        logger.info("Task classified for agents: %s", [t.value for t in matched])
        return matched

    @staticmethod
    def should_continue(state: WorkflowState) -> str:
        """Determine the next node in the workflow graph.

        Args:
            state: The current workflow state.

        Returns:
            Name of the next node: "aggregate" if no errors, "handle_error" if errors.
        """
        errors = state.get("errors", [])
        agent_outputs = state.get("agent_outputs", [])

        # If all agents failed, go to error handler
        if errors and not agent_outputs:
            return "handle_error"

        # If we have some outputs (even with some errors), aggregate
        return "aggregate"
