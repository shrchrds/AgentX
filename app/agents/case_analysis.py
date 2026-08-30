"""Case Analysis Agent.

Specialized agent for analyzing legal cases — identifying precedents,
evaluating arguments, and providing legal insights.
"""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.base import LegalAgent
from app.core.logging import set_agent_context, set_task_context
from app.models.agent import AgentResponse, AgentType

logger = logging.getLogger(__name__)

_SYSTEM_INSTRUCTIONS = (
    "You are a legal case analysis specialist. "
    "Analyze legal cases, identify precedents, evaluate arguments, and provide legal insights. "
    "Provide structured analysis with clear sections: "
    "1) Case Summary, 2) Key Legal Issues, 3) Relevant Precedents, 4) Analysis, 5) Recommendations."
)


class CaseAnalysisAgent(LegalAgent):
    """Agent specialized in legal case analysis and precedent research."""

    def __init__(self, agent_id: str, memory, llm=None) -> None:
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.CASE_ANALYSIS,
            memory=memory,
            llm=llm,
        )

    def _get_description(self) -> str:
        return "Analyzes legal cases, identifies precedents, and provides legal insights."

    async def process_input(self, task_id: str, input_data: str, context: dict) -> AgentResponse:
        set_task_context(task_id)
        set_agent_context(self.agent_id)
        logger.info("CaseAnalysisAgent processing task")

        try:
            # Load existing context from memory
            history = await self.memory.load_context(self.agent_id, task_id)

            # Build messages
            system_prompt = self._build_system_prompt(_SYSTEM_INSTRUCTIONS)
            messages = [SystemMessage(content=system_prompt)]

            for record in history:
                if "role" in record.data and "content" in record.data:
                    messages.append(HumanMessage(content=record.data["content"]))

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

            logger.info("CaseAnalysisAgent completed task")
            return AgentResponse(
                task_id=task_id,
                agent_id=self.agent_id,
                output_data=output,
                status="completed",
            )

        except Exception as e:
            logger.error("CaseAnalysisAgent failed: %s", str(e))
            return AgentResponse(
                task_id=task_id,
                agent_id=self.agent_id,
                output_data="",
                status="failed",
                errors=[f"Case analysis failed: {type(e).__name__}"],
            )
