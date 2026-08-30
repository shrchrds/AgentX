"""Risk Analysis Agent.

Specialized agent for evaluating legal risks — compliance gaps,
regulatory exposure, and liability assessment.
"""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.base import LegalAgent
from app.core.logging import set_agent_context, set_task_context
from app.models.agent import AgentResponse, AgentType

logger = logging.getLogger(__name__)

_SYSTEM_INSTRUCTIONS = (
    "You are a legal risk analysis specialist. "
    "Evaluate legal risks, compliance gaps, regulatory exposure, and liability. "
    "Provide structured analysis with clear sections: "
    "1) Risk Summary, 2) Compliance Assessment, 3) Regulatory Exposure, "
    "4) Liability Analysis, 5) Mitigation Recommendations."
)


class RiskAnalysisAgent(LegalAgent):
    """Agent specialized in legal risk evaluation and compliance analysis."""

    def __init__(self, agent_id: str, memory, llm=None) -> None:
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.RISK_ANALYSIS,
            memory=memory,
            llm=llm,
        )

    def _get_description(self) -> str:
        return "Evaluates legal risks, compliance gaps, regulatory exposure, and liability."

    async def process_input(self, task_id: str, input_data: str, context: dict) -> AgentResponse:
        set_task_context(task_id)
        set_agent_context(self.agent_id)
        logger.info("RiskAnalysisAgent processing task")

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

            logger.info("RiskAnalysisAgent completed task")
            return AgentResponse(
                task_id=task_id,
                agent_id=self.agent_id,
                output_data=output,
                status="completed",
            )

        except Exception as e:
            logger.error("RiskAnalysisAgent failed: %s", str(e))
            return AgentResponse(
                task_id=task_id,
                agent_id=self.agent_id,
                output_data="",
                status="failed",
                errors=[f"Risk analysis failed: {type(e).__name__}"],
            )
