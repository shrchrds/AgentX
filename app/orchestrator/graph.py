"""LangGraph-based orchestrator for multi-agent workflows.

Builds a StateGraph with classify → execute → aggregate/error nodes.
Manages the full lifecycle of a task through multiple specialized agents.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from langgraph.graph import END, StateGraph

from app.agents.manager import AgentManager
from app.core.logging import set_task_context
from app.models.task import TaskRequest, TaskResponse, TaskStatus
from app.orchestrator.router import TaskRouter
from app.orchestrator.state import WorkflowState, initialize_state

logger = logging.getLogger(__name__)

# Default timeout for the entire workflow (seconds)
_WORKFLOW_TIMEOUT = 300


class AgentOrchestrator:
    """LangGraph-powered orchestrator for multi-agent legal task processing.

    Builds a StateGraph with the following flow:
        START → classify → execute_agents → aggregate → END
                                          → handle_error → END

    Args:
        agent_manager: The agent registry and lifecycle manager.
        timeout: Maximum seconds to wait for workflow completion.
    """

    def __init__(self, agent_manager: AgentManager, timeout: int = _WORKFLOW_TIMEOUT) -> None:
        self._agent_manager = agent_manager
        self._router = TaskRouter()
        self._timeout = timeout
        self._graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Construct the LangGraph StateGraph."""
        graph = StateGraph(WorkflowState)

        # Add nodes
        graph.add_node("classify", self._classify_node)
        graph.add_node("execute_agents", self._execute_agents_node)
        graph.add_node("aggregate", self._aggregate_node)
        graph.add_node("handle_error", self._handle_error_node)

        # Set entry point
        graph.set_entry_point("classify")

        # Add edges
        graph.add_edge("classify", "execute_agents")
        graph.add_conditional_edges(
            "execute_agents",
            self._router.should_continue,
            {
                "aggregate": "aggregate",
                "handle_error": "handle_error",
            },
        )
        graph.add_edge("aggregate", END)
        graph.add_edge("handle_error", END)

        return graph

    async def _classify_node(self, state: WorkflowState) -> dict:
        """Classify the task and determine target agent types."""
        set_task_context(state["task_id"])
        logger.info("Classifying task")

        agent_types = self._router.classify_task(state["input_data"], state.get("metadata", {}))

        return {
            "target_agent_types": [t.value for t in agent_types],
            "status": TaskStatus.RUNNING,
        }

    async def _execute_agents_node(self, state: WorkflowState) -> dict:
        """Execute all target agents and collect their responses."""
        set_task_context(state["task_id"])
        logger.info("Executing agents: %s", state.get("target_agent_types", []))

        target_types = state.get("target_agent_types", [])
        agents = []

        for agent in self._agent_manager.list_agents():
            if agent.agent_type in target_types:
                try:
                    agents.append(self._agent_manager.get_agent(agent.agent_id))
                except KeyError:
                    continue

        if not agents:
            return {
                "errors": ["No agents available for the requested task types"],
                "agent_outputs": [],
            }

        # Execute all agents concurrently
        tasks = [
            agent.process_input(
                state["task_id"],
                state["input_data"],
                state.get("metadata", {}),
            )
            for agent in agents
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        outputs: list[dict] = []
        errors: list[str] = []

        for result in results:
            if isinstance(result, Exception):
                errors.append(f"Agent execution error: {type(result).__name__}")
            elif result.status == "failed":
                errors.extend(result.errors)
            else:
                outputs.append(result.model_dump())

        return {
            "agent_outputs": outputs,
            "errors": errors,
        }

    async def _aggregate_node(self, state: WorkflowState) -> dict:
        """Aggregate agent outputs into a final response."""
        set_task_context(state["task_id"])
        logger.info("Aggregating %d agent outputs", len(state.get("agent_outputs", [])))

        outputs = state.get("agent_outputs", [])
        errors = state.get("errors", [])

        if not outputs:
            return {
                "final_output": "No analysis results available.",
                "status": TaskStatus.FAILED,
                "errors": errors or ["No agent outputs to aggregate"],
            }

        # Build aggregated output
        sections: list[str] = []
        for output in outputs:
            agent_id = output.get("agent_id", "Unknown Agent")
            data = output.get("output_data", "")
            if data:
                sections.append(f"## Analysis by {agent_id}\n\n{data}")

        final = "\n\n---\n\n".join(sections)

        if errors:
            final += "\n\n---\n\n### Warnings\n\n" + "\n".join(f"- {e}" for e in errors)

        return {
            "final_output": final,
            "status": TaskStatus.COMPLETED,
        }

    async def _handle_error_node(self, state: WorkflowState) -> dict:
        """Handle workflow errors and produce a failure response."""
        set_task_context(state["task_id"])
        errors = state.get("errors", [])
        logger.error("Workflow failed with errors: %s", errors)

        return {
            "final_output": "",
            "status": TaskStatus.FAILED,
            "errors": errors or ["Unknown workflow error"],
        }

    async def run_workflow(self, task: TaskRequest) -> TaskResponse:
        """Execute the full orchestration workflow for a task.

        Args:
            task: The incoming task request.

        Returns:
            TaskResponse with the aggregated results.
        """
        set_task_context(task.task_id)
        logger.info("Starting workflow for task: %s", task.task_id)

        initial_state = initialize_state(task)
        compiled = self._graph.compile()

        try:
            final_state = await asyncio.wait_for(
                compiled.ainvoke(initial_state),
                timeout=self._timeout,
            )

            return TaskResponse(
                task_id=task.task_id,
                status=TaskStatus(final_state.get("status", TaskStatus.FAILED)),
                output_data=final_state.get("final_output"),
                errors=final_state.get("errors", []),
                completed_at=datetime.now(timezone.utc),
            )

        except asyncio.TimeoutError:
            logger.error("Workflow timed out for task: %s", task.task_id)
            return TaskResponse(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                output_data=None,
                errors=["Workflow timed out"],
                completed_at=datetime.now(timezone.utc),
            )
        except Exception as e:
            logger.error("Workflow failed: %s", str(e))
            return TaskResponse(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                output_data=None,
                errors=[f"Workflow error: {type(e).__name__}"],
                completed_at=datetime.now(timezone.utc),
            )
