"""Command-line interface for AgentX.

Allows running legal tasks, listing agents, and running automated demos
directly from the terminal.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timezone

from app.agents.manager import AgentManager
from app.core.config import settings
from app.core.logging import setup_logging
from app.memory.store import create_memory_store
from app.models.task import TaskRequest
from app.orchestrator.graph import AgentOrchestrator

SAMPLE_LEGAL_TASKS = {
    "nda": (
        "Review the following Non-Disclosure Agreement clause: 'Recipient agrees to hold "
        "all proprietary information strictly confidential in perpetuity, without exception, "
        "and agrees to pay liquidated damages of $1,000,000 for any disclosure regardless "
        "of intent. Governing law shall be the State of Delaware.'"
    ),
    "non_compete": (
        "Assess the enforceability and risk of a nationwide non-compete restriction lasting "
        "5 years for a senior software engineer moving to a competitor in California."
    ),
    "liability": (
        "Analyze liability and dispute resolution terms in an enterprise SaaS agreement where "
        "consequential damages are un-capped and arbitration is mandatory in London under "
        "ICC rules."
    ),
}


async def run_task_async(input_text: str, task_id: str | None = None) -> None:
    """Execute a legal task through the orchestrator and print formatted results."""
    task_id = task_id or f"cli-{int(datetime.now(timezone.utc).timestamp())}"

    print("\n" + "=" * 60)
    print("  AgentX Multi-Agent Legal Task Execution")
    print(f"  Task ID: {task_id}")
    print("=" * 60)
    print(f"\n[Input Query/Text]:\n{input_text.strip()}\n")
    print("-" * 60)
    print("Initializing agents & memory store...")

    memory_store = create_memory_store(settings.memory_backend)
    manager = AgentManager(memory_store=memory_store)
    orchestrator = AgentOrchestrator(agent_manager=manager)

    print(f"Registered Agents: {', '.join(manager._registry.keys())}")
    print("Orchestrator routing and executing agents...")

    req = TaskRequest(task_id=task_id, input_data=input_text)
    start_time = datetime.now(timezone.utc)
    response = await orchestrator.run_workflow(req)
    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

    print(f"\nCompleted in {elapsed:.2f}s | Status: {response.status.upper()}")
    if response.errors:
        print(f"Warnings/Errors: {response.errors}")

    print("\n" + "=" * 60)
    print("  Aggregated Analysis Output")
    print("=" * 60 + "\n")
    print(response.output_data or "No output returned.")
    print("\n" + "=" * 60 + "\n")


def main() -> None:
    """CLI entrypoint."""
    setup_logging("WARNING")

    parser = argparse.ArgumentParser(
        description="AgentX: Multi-Agent Legal Collaboration Framework CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Run a demo legal review task")
    demo_parser.add_argument(
        "--type",
        choices=["nda", "non_compete", "liability"],
        default="nda",
        help="Sample legal query to execute (default: nda)",
    )

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a custom legal query")
    run_parser.add_argument("query", type=str, help="Legal text or prompt to analyze")
    run_parser.add_argument("--task-id", type=str, default=None, help="Custom task ID")

    # List agents command
    subparsers.add_parser("list-agents", help="List registered agents and capabilities")

    args = parser.parse_args()

    if args.command == "demo":
        sample = SAMPLE_LEGAL_TASKS[args.type]
        asyncio.run(run_task_async(sample, task_id=f"demo-{args.type}"))
    elif args.command == "run":
        asyncio.run(run_task_async(args.query, task_id=args.task_id))
    elif args.command == "list-agents":
        memory_store = create_memory_store(settings.memory_backend)
        manager = AgentManager(memory_store=memory_store)
        print("\nAgentX Registered Legal Agents:")
        print("-" * 50)
        for agent_info in manager.list_agents():
            print(f"• ID: {agent_info.agent_id}")
            print(f"  Type: {agent_info.agent_type}")
            print(f"  Description: {agent_info.description}")
            print("-" * 50)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
