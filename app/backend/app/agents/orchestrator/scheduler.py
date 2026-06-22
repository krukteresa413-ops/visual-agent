"""Task scheduler — executes DAG task graphs with concurrency control.

P2.4: Added conditional branching (alternative agents) and per-node retry.
"""
import asyncio
from typing import Dict

from app.agents.orchestrator.task_graph import TaskGraph, TaskNode
from app.agents.orchestrator.agent_factory import AgentFactory


class TaskScheduler:
    """Executes a TaskGraph with bounded concurrency."""

    def __init__(self, max_concurrent: int = 3, max_retries: int = 3):
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries

    async def execute(self, graph: TaskGraph, project_id: str) -> Dict:
        """Run all tasks in the graph, respecting dependencies and concurrency limit."""
        while True:
            ready = graph.get_ready_tasks(self.max_concurrent)
            if not ready:
                pending = any(n.status == "pending" for n in graph.nodes.values())
                if not pending:
                    break
                failed = any(n.status == "failed" for n in graph.nodes.values())
                if failed or not pending:
                    break

            tasks = [
                self._run_task(graph.nodes[tid], project_id)
                for tid in ready
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for tid, result in zip(ready, results):
                if isinstance(result, Exception):
                    graph.mark_failed(tid, str(result))
                else:
                    graph.mark_complete(tid, result)

        all_success = all(
            node.status == "success" for node in graph.nodes.values()
        )
        return {"success": all_success}

    async def _run_task(self, node: TaskNode, project_id: str) -> Dict:
        """Execute a single task with retry and conditional branching.

        P2.4: If primary agent_type fails all retries, try alternatives in order.
        Per-node max_retries overrides scheduler global.
        """
        # Resolve effective max_retries: node-level > scheduler global
        effective_retries = (
            node.max_retries if node.max_retries is not None
            else self.max_retries
        )

        # Build the list of agent types to try: primary + alternatives
        agent_types = [node.agent_type] + node.alternatives

        last_error = None
        for agent_type in agent_types:
            try:
                return await self._try_agent(agent_type, node, project_id, effective_retries)
            except Exception as e:
                node.retry_count = 0  # reset for next agent type
                last_error = e
                continue

        # All agent types exhausted
        raise last_error or RuntimeError(f"All agents failed for task {node.id}")

    async def _try_agent(
        self, agent_type: str, node: TaskNode, project_id: str, max_retries: int
    ) -> Dict:
        """Try a single agent type with retries and exponential backoff."""
        for attempt in range(max_retries):
            try:
                agent = AgentFactory.create(agent_type, node.params)
                result = await agent(project_id=project_id, **node.params)
                return result
            except Exception as e:
                node.retry_count += 1
                if attempt == max_retries - 1:
                    raise
                # Exponential backoff: 2^attempt seconds
                delay = 2 ** attempt
                await asyncio.sleep(delay)
