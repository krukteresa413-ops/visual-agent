"""Task scheduler — executes DAG task graphs with concurrency control."""
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
                self._run_task(graph.nodes[tid], project_id, graph)
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

    async def _run_task(self, node: TaskNode, project_id: str, graph: TaskGraph) -> Dict:
        """Execute a single task via its agent."""
        for attempt in range(self.max_retries):
            try:
                agent = AgentFactory.create(node.agent_type, node.params)
                result = await agent(project_id=project_id, **node.params)
                return result
            except Exception as e:
                node.retry_count += 1
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
