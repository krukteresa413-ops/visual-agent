"""DAG task graph — models task nodes and their dependencies."""
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class TaskNode:
    """A single task in the DAG."""
    id: str
    agent_type: str
    dependencies: List[str] = field(default_factory=list)
    params: Dict = field(default_factory=dict)
    status: str = "pending"
    retry_count: int = 0


class TaskGraph:
    """Directed acyclic graph of tasks with dependency resolution."""

    def __init__(self):
        self.nodes: Dict[str, TaskNode] = {}

    def add_task(self, node: TaskNode) -> None:
        if self._has_cycle(node):
            raise ValueError(f"Adding task {node.id} would create a cycle")
        self.nodes[node.id] = node

    def _has_cycle(self, new_node: TaskNode) -> bool:
        """Check if adding this node would create a cycle."""
        temp_nodes = {**self.nodes, new_node.id: new_node}
        visited = set()
        rec_stack = set()
        
        def visit(nid: str) -> bool:
            if nid in rec_stack:
                return True
            if nid in visited:
                return False
            visited.add(nid)
            rec_stack.add(nid)
            for dep in temp_nodes[nid].dependencies:
                if dep in temp_nodes and visit(dep):
                    return True
            rec_stack.remove(nid)
            return False
        
        return visit(new_node.id)

    def get_ready_tasks(self, max_concurrent: int = 3) -> List[str]:
        ready = [
            nid for nid, node in self.nodes.items()
            if self._is_ready(node)
        ]
        return ready[:max_concurrent]

    def _is_ready(self, node: TaskNode) -> bool:
        """A task is ready if it's pending and all dependencies have succeeded."""
        if node.status != "pending":
            return False
        return all(
            dep in self.nodes and self.nodes[dep].status == "success"
            for dep in node.dependencies
        )

    def mark_complete(self, task_id: str, result: Dict) -> None:
        self.nodes[task_id].status = "success"

    def mark_failed(self, task_id: str, error: str) -> None:
        self.nodes[task_id].status = "failed"
