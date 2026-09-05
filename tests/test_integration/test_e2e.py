"""End-to-end integration tests for AgentX.

Tests the full orchestration workflow using the public API:
orchestrator.run_workflow(TaskRequest) → TaskResponse.
"""

import asyncio

import pytest
from langchain_core.language_models import FakeListChatModel

from app.agents.manager import AgentManager
from app.models.agent import AgentResponse, AgentType
from app.models.task import TaskRequest, TaskStatus
from app.orchestrator.graph import AgentOrchestrator


class TestE2EWorkflow:
    """End-to-end workflow tests via orchestrator.run_workflow()."""

    @pytest.mark.asyncio
    async def test_full_workflow_contract_review(self, orchestrator, mock_llm):
        """Test full workflow: submit task → orchestrator processes → get result."""
        # Create a task that should trigger CONTRACT_REVIEW agent
        task = TaskRequest(
            task_id="test-task-001",
            input_data="Review the NDA contract for compliance issues",
        )

        result = await orchestrator.run_workflow(task)

        # Verify workflow completed successfully
        assert result.status == TaskStatus.COMPLETED
        assert result.output_data is not None
        assert result.output_data != ""
        assert result.task_id == "test-task-001"
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_full_workflow_multi_agent(self, memory_store):
        """Test workflow with multiple agents activated."""
        # Setup mock with multiple responses for different agents
        mock_llm_multi = FakeListChatModel(
            responses=[
                "Contract analysis: NDA is compliant.",
                "Case analysis: Similar cases found.",
                "Risk assessment: Low risk overall.",
            ]
        )

        agent_manager = AgentManager(memory_store=memory_store, llm=mock_llm_multi)
        for agent in agent_manager._registry.values():
            agent._llm = mock_llm_multi

        orchestrator = AgentOrchestrator(agent_manager=agent_manager)

        # Task with keywords that trigger multiple agents
        task = TaskRequest(
            task_id="test-task-002",
            input_data="Analyze contract liability and risk factors with case precedents",
        )

        result = await orchestrator.run_workflow(task)

        # Should activate multiple agents based on keywords
        assert result.status == TaskStatus.COMPLETED
        assert result.output_data is not None
        assert len(result.errors) == 0
        # Output should contain sections from multiple agents
        assert "##" in result.output_data  # Multiple agent sections

    @pytest.mark.asyncio
    async def test_workflow_with_error_handling(self, memory_store):
        """Test workflow error handling when all agents fail."""
        # Create an agent manager with agents that will fail
        agent_manager = AgentManager(memory_store=memory_store)

        # Patch all agents to fail
        for agent in agent_manager._registry.values():

            async def failing_process(*args, **kwargs):
                return AgentResponse(
                    task_id=args[0],
                    agent_id="mock-agent",
                    output_data="",
                    status="failed",
                    errors=["Agent execution failed"],
                )

            agent.process_input = failing_process

        orchestrator = AgentOrchestrator(agent_manager=agent_manager)

        task = TaskRequest(
            task_id="test-task-003",
            input_data="Review contract",
        )

        result = await orchestrator.run_workflow(task)

        # Should handle error gracefully
        assert result.status == TaskStatus.FAILED
        assert len(result.errors) > 0
        assert any("failed" in err.lower() for err in result.errors)

    @pytest.mark.asyncio
    async def test_workflow_partial_failure(self, memory_store):
        """Test workflow when some agents succeed and others fail."""
        mock_llm = FakeListChatModel(
            responses=["Successful contract analysis with detailed findings."]
        )

        agent_manager = AgentManager(memory_store=memory_store, llm=mock_llm)

        # Make CONTRACT_REVIEW succeed (keep mock LLM), others fail
        for agent in agent_manager._registry.values():
            if agent.agent_type == AgentType.CONTRACT_REVIEW:
                agent._llm = mock_llm
            else:

                async def failing_process(*args, **kwargs):
                    return AgentResponse(
                        task_id=args[0],
                        agent_id="mock-agent",
                        output_data="",
                        status="failed",
                        errors=["Agent failed"],
                    )

                agent.process_input = failing_process

        orchestrator = AgentOrchestrator(agent_manager=agent_manager)

        task = TaskRequest(
            task_id="test-task-004",
            input_data="Review contract compliance and analyze case precedents",
        )

        result = await orchestrator.run_workflow(task)

        # Should aggregate successful results with warnings
        assert result.status == TaskStatus.COMPLETED
        assert result.output_data is not None
        # Should contain warnings section for partial failures
        assert "Warning" in result.output_data or len(result.errors) > 0


class TestConcurrentTaskSubmissions:
    """Test concurrent task handling."""

    @pytest.mark.asyncio
    async def test_concurrent_task_submissions(self, orchestrator):
        """Test multiple concurrent task submissions."""
        # Create multiple tasks
        tasks = [
            TaskRequest(
                task_id=f"concurrent-task-{i}",
                input_data=f"Review contract number {i}",
            )
            for i in range(5)
        ]

        # Execute all tasks concurrently
        results = await asyncio.gather(*[orchestrator.run_workflow(task) for task in tasks])

        # Verify all tasks completed
        assert len(results) == 5
        for result in results:
            assert result.status == TaskStatus.COMPLETED
            assert result.output_data is not None
            assert result.output_data != ""

    @pytest.mark.asyncio
    async def test_concurrent_different_task_types(self, memory_store):
        """Test concurrent submissions of different task types."""
        mock_llm_multi = FakeListChatModel(
            responses=[f"Response {i}" for i in range(15)]  # 3 tasks × ~5 agents each
        )

        agent_manager = AgentManager(memory_store=memory_store, llm=mock_llm_multi)
        for agent in agent_manager._registry.values():
            agent._llm = mock_llm_multi

        orchestrator = AgentOrchestrator(agent_manager=agent_manager)

        tasks = [
            TaskRequest(
                task_id="task-contract",
                input_data="Review NDA contract",
            ),
            TaskRequest(
                task_id="task-case",
                input_data="Analyze patent infringement case",
            ),
            TaskRequest(
                task_id="task-risk",
                input_data="Assess litigation risk",
            ),
        ]

        results = await asyncio.gather(*[orchestrator.run_workflow(task) for task in tasks])

        assert len(results) == 3
        for result in results:
            assert result.status == TaskStatus.COMPLETED
            assert result.output_data is not None


class TestAgentHotPlug:
    """Test dynamic agent registration and usage."""

    @pytest.mark.asyncio
    async def test_register_new_agent_and_use(self, memory_store, mock_llm):
        """Test registering a new agent and verifying it's used in tasks."""
        agent_manager = AgentManager(memory_store=memory_store, llm=mock_llm)

        # Register a second contract review agent
        info = agent_manager.register_agent(
            AgentType.CONTRACT_REVIEW, agent_id="custom-contract-001"
        )

        # Verify it was registered
        agents = agent_manager.list_agents()
        contract_agents = [a for a in agents if a.agent_type == AgentType.CONTRACT_REVIEW]
        assert len(contract_agents) == 2  # Default + custom
        assert any(a.agent_id == "custom-contract-001" for a in contract_agents)

        # Verify agent info
        assert info.agent_id == "custom-contract-001"
        assert info.agent_type == AgentType.CONTRACT_REVIEW

    @pytest.mark.asyncio
    async def test_remove_agent(self, agent_manager):
        """Test removing an agent from the manager."""
        # Get initial agent count
        initial_agents = agent_manager.list_agents()
        contract_agents = [a for a in initial_agents if a.agent_type == AgentType.CONTRACT_REVIEW]
        initial_count = len(contract_agents)
        assert initial_count > 0

        # Remove first contract agent
        agent_to_remove = contract_agents[0]
        agent_manager.remove_agent(agent_to_remove.agent_id)

        # Verify it was removed
        remaining_agents = agent_manager.list_agents()
        remaining_contract = [
            a for a in remaining_agents if a.agent_type == AgentType.CONTRACT_REVIEW
        ]
        assert len(remaining_contract) == initial_count - 1
        assert not any(a.agent_id == agent_to_remove.agent_id for a in remaining_contract)

    @pytest.mark.asyncio
    async def test_orchestrator_uses_newly_registered_agent(self, memory_store, mock_llm):
        """Test that orchestrator picks up newly registered agents."""
        agent_manager = AgentManager(memory_store=memory_store, llm=mock_llm)
        orchestrator = AgentOrchestrator(agent_manager=agent_manager)

        # Register a new agent with identifiable output
        mock_llm_identifiable = FakeListChatModel(
            responses=["IDENTIFIABLE_OUTPUT: Special agent executed"]
        )
        agent_manager.register_agent(AgentType.CONTRACT_REVIEW, agent_id="identifiable-001")
        identifiable_agent = agent_manager.get_agent("identifiable-001")
        identifiable_agent._llm = mock_llm_identifiable

        # Run a task
        task = TaskRequest(
            task_id="test-new-agent",
            input_data="Review contract terms",
        )

        result = await orchestrator.run_workflow(task)

        # Verify the workflow completed successfully
        assert result.status == TaskStatus.COMPLETED
        assert result.output_data is not None
        # The new agent should have contributed (its output should be in the final aggregation)
        assert (
            "IDENTIFIABLE_OUTPUT" in result.output_data or "identifiable-001" in result.output_data
        )


class TestMemoryIntegration:
    """Test memory integration across workflow."""

    @pytest.mark.asyncio
    async def test_memory_persists_across_agents(self, orchestrator, memory_store):
        """Test that memory is shared across agents for the same task."""
        task_id = "memory-test-001"

        # First execution
        task1 = TaskRequest(
            task_id=task_id,
            input_data="Review NDA contract clause 5",
        )

        result1 = await orchestrator.run_workflow(task1)
        assert result1.status == TaskStatus.COMPLETED

        # Second execution with same task_id (simulating follow-up)
        task2 = TaskRequest(
            task_id=task_id,
            input_data="What about clause 6?",
        )

        result2 = await orchestrator.run_workflow(task2)
        assert result2.status == TaskStatus.COMPLETED

        # Verify memory was used by checking that agents have stored context
        # Get all agents and check if any have memory for this task
        agents = orchestrator._agent_manager.list_agents()
        memory_found = False
        for agent_info in agents:
            agent = orchestrator._agent_manager.get_agent(agent_info.agent_id)
            memory_entries = await agent.memory.load_context(agent.agent_id, task_id)
            if len(memory_entries) > 0:
                memory_found = True
                break

        assert memory_found, "No memory entries found for the task"


class TestTimeout:
    """Test timeout handling."""

    @pytest.mark.asyncio
    async def test_agent_timeout(self, memory_store):
        """Test that orchestrator workflow respects timeout."""
        agent_manager = AgentManager(memory_store=memory_store)

        # Make all agents slow
        for agent in agent_manager._registry.values():

            async def slow_process(task_id, input_data, context):
                await asyncio.sleep(10)  # Longer than timeout
                return AgentResponse(
                    task_id=task_id,
                    agent_id="slow-agent",
                    output_data="This should timeout",
                    status="completed",
                )

            agent.process_input = slow_process

        # Use a short timeout
        orchestrator = AgentOrchestrator(agent_manager=agent_manager, timeout=1)

        task = TaskRequest(
            task_id="timeout-test",
            input_data="Review contract",
        )

        result = await orchestrator.run_workflow(task)

        # Should complete with timeout error
        assert result.status == TaskStatus.FAILED
        assert len(result.errors) > 0
        assert any("timed out" in err.lower() for err in result.errors)
