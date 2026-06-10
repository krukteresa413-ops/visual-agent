"""
TDD Step 1 (RED): 3 failing tests for TaskGraph.

Run: pytest tests/unit/orchestrator/test_task_graph.py -v
Expected: 3 FAILED (module not found)
"""
import pytest
from app.agents.orchestrator.task_graph import TaskGraph, TaskNode


def test_add_task_node():
    """添加任务节点后，图中应包含该节点。"""
    graph = TaskGraph()
    node = TaskNode(id="t1", agent_type="visual", dependencies=[], params={})
    graph.add_task(node)
    assert len(graph.nodes) == 1
    assert "t1" in graph.nodes


def test_get_ready_tasks_respects_dependencies():
    """t2 依赖 t1，t1 未完成时 t2 不应返回为就绪任务。"""
    graph = TaskGraph()
    graph.add_task(TaskNode(id="t1", agent_type="visual", dependencies=[], params={}))
    graph.add_task(TaskNode(id="t2", agent_type="layout", dependencies=["t1"], params={}))

    # t1 应该就绪，t2 不应该
    ready = graph.get_ready_tasks()
    assert ready == ["t1"]

    # 完成 t1 后，t2 应该就绪
    graph.mark_complete("t1", {"result": "ok"})
    ready = graph.get_ready_tasks()
    assert ready == ["t2"]


def test_max_concurrent_limit():
    """添加5个无依赖任务，max_concurrent=3 时只返回3个就绪任务。"""
    graph = TaskGraph()
    for i in range(5):
        graph.add_task(TaskNode(id=f"t{i}", agent_type="visual", dependencies=[], params={}))

    ready = graph.get_ready_tasks(max_concurrent=3)
    assert len(ready) == 3
    # 返回的应该是前3个 pending 任务
    assert set(ready) == {"t0", "t1", "t2"}
