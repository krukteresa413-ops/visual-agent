"""
TDD Step 1 (RED): 2 failing tests for TaskScheduler.
Uses unittest.mock (project standard).
"""
import asyncio
from unittest.mock import patch, MagicMock
import pytest
from app.agents.orchestrator.task_graph import TaskGraph, TaskNode


@pytest.mark.asyncio
async def test_scheduler_executes_tasks_in_order():
    """验证调度器按依赖顺序执行：t1 完成前 t2 不启动。"""
    execution_order = []

    async def fake_agent(project_id=None, **kwargs):
        task_id = kwargs.get("_task_id", "unknown")
        execution_order.append(task_id)
        await asyncio.sleep(0.01)
        return {"status": "ok", "task_id": task_id}

    with patch(
        "app.agents.orchestrator.agent_factory.AgentFactory.create",
        return_value=fake_agent,
    ):
        from app.agents.orchestrator.scheduler import TaskScheduler

        graph = TaskGraph()
        graph.add_task(TaskNode(id="t1", agent_type="visual", dependencies=[], params={"_task_id": "t1"}))
        graph.add_task(TaskNode(id="t2", agent_type="layout", dependencies=["t1"], params={"_task_id": "t2"}))

        scheduler = TaskScheduler()
        result = await scheduler.execute(graph, project_id="p1")

        assert result["success"] is True
        assert execution_order == ["t1", "t2"]


@pytest.mark.asyncio
async def test_scheduler_respects_max_concurrent():
    """验证调度器不会超过 max_concurrent=3 的并发限制。"""
    active_count = 0
    max_active = 0
    lock = asyncio.Lock()

    async def fake_agent(project_id=None, **kwargs):
        nonlocal active_count, max_active
        async with lock:
            active_count += 1
            max_active = max(max_active, active_count)
        await asyncio.sleep(0.05)
        async with lock:
            active_count -= 1
        return {}

    with patch(
        "app.agents.orchestrator.agent_factory.AgentFactory.create",
        return_value=fake_agent,
    ):
        from app.agents.orchestrator.scheduler import TaskScheduler

        graph = TaskGraph()
        for i in range(6):
            graph.add_task(TaskNode(id=f"t{i}", agent_type="visual", dependencies=[], params={}))

        scheduler = TaskScheduler(max_concurrent=3)
        await scheduler.execute(graph, project_id="p1")

        assert max_active <= 3, f"Expected max 3 concurrent, got {max_active}"
        assert all(n.status == "success" for n in graph.nodes.values())
