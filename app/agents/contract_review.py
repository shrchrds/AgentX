"""Contract Review Agent.

Specialized agent for analyzing legal contracts — identifying risks,
missing clauses, ambiguities, and compliance issues.
"""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.base import LegalAgent
from app.core.logging import set_agent_context, set_task_context
from app.models.agent import AgentResponse, AgentType

logger = logging.getLogger(__name__)

_SYSTEM_INSTRUCTIONS = (
    "You are a legal contract review specialist. "
    "Analyze contracts for risks, missing clauses, ambiguities, and compliance issues. "
    "Provide structured analysis with clear sections: "
    "1) Summary, 2) Key Risks, 3) Missing Clauses, 4) Recommendations."
)


class ContractReviewAgent(LegalAgent):
    """Agent specialized in legal contract review and analysis."""

    def __init__(self, agent_id: str, memory, llm=None) -> None:
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.CONTRACT_REVIEW,
            memory=memory,
            llm=llm,
        )

    def _get_description(self) -> str:
        return "Analyzes legal contracts for risks, missing clauses, ambiguities, and compliance."

    async def process_input(self, task_id: str, input_data: str, context: dict) -> AgentResponse:
        set_task_context(task_id)
        set_agent_context(self.agent_id)
        logger.info("ContractReviewAgent processing task")

        try:
            # Load existing context from memory
            history = await self.memory.load_context(self.agent_id, task_id)

            # Build messages
            system_prompt = self._build_system_prompt(_SYSTEM_INSTRUCTIONS)
            messages = [SystemMessage(content=system_prompt)]

            # Add history
            for record in history:
                if "role" in record.data and "content" in record.data:
                    messages.append(HumanMessage(content=record.data["content"]))

            # Add current input
            messages.append(HumanMessage(content=input_data))

            # Call LLM
            response = await self.llm.ainvoke(messages)
            output = self._sanitize_output(response.content)

            # Save to memory
            await self.memory.save_context(
                self.agent_id,
                task_id,
                {"role": "assistant", "content": output, "task_id": task_id},
            )

            logger.info("ContractReviewAgent completed task")
            return AgentResponse(
                task_id=task_id,
                agent_id=self.agent_id,
                output_data=output,
                status="completed",
            )

        except Exception as e:
            logger.error("ContractReviewAgent failed: %s", str(e))
            return AgentResponse(
                task_id=task_id,
                agent_id=self.agent_id,
                output_data="",
                status="failed",
                errors=[f"Contract review failed: {type(e).__name__}"],
            )
