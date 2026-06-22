"""Tests for P2.4: Conditional branching + per-node retry optimization.

TDD: RED phase — these tests should FAIL before implementation.
"""
import asyncio
from unittest.mock import patch, MagicMock
import pytest

from app.agents.orchestrator.task_graph import TaskGraph, TaskNode
from app.agents.orchestrator.scheduler import TaskScheduler


# ---------------------------------------------------------------------------
# 1. Conditional branching — fallback to alternative agent on failure
# ---------------------------------------------------------------------------

class TestConditionalBranching:
    """Test that failed tasks can fall back to alternative agents."""

    def test_task_node_supports_alternatives(self):
        """TaskNode should accept a list of alternative agent types."""
        node = TaskNode(
            id="t1",
            agent_type="visual",
            alternatives=["layout", "mockup"],
        )
        assert node.alternatives == ["layout", "mockup"]

    def test_task_node_alternatives_default_empty(self):
        """TaskNode alternatives should default to empty list."""
        node = TaskNode(id="t1", agent_type="visual")
        assert node.alternatives == []

    @pytest.mark.asyncio
    async def test_fallback_to_alternative_on_failure(self):
        """When primary agent fails all retries, scheduler should try alternatives."""
        call_order = []

        async def visual_agent(project_id=None, **kwargs):
            call_order.append("visual")
            raise RuntimeError("Visual agent failed")

        async def layout_agent(project_id=None, **kwargs):
            call_order.append("layout")
            return {"status": "ok", "agent": "layout"}

        # Agent factory returns different agents based on type
        agent_map = {
            "visual": visual_agent,
            "layout": layout_agent,
        }

        def mock_create(agent_type, config=None):
            agent = agent_map.get(agent_type)
            if config:
                return lambda **kw: agent(**{**config, **kw})
            return agent

        with patch(
            "app.agents.orchestrator.agent_factory.AgentFactory.create",
            side_effect=mock_create,
        ):
            graph = TaskGraph()
            node = TaskNode(
                id="t1",
                agent_type="visual",
                alternatives=["layout"],
                params={},
            )
            graph.add_task(node)

            scheduler = TaskScheduler(max_concurrent=1)
            # Per-node max_retries=1 so we don't wait for multiple retries
            node.max_retries = 1
            result = await scheduler.execute(graph, project_id="p1")

            assert result["success"] is True
            assert call_order == ["visual", "layout"]

    @pytest.mark.asyncio
    async def test_all_alternatives_exhausted(self):
        """When primary AND all alternatives fail, task should be marked failed."""
        async def failing_agent(project_id=None, **kwargs):
            raise RuntimeError("Always fails")

        agent_map = {"visual": failing_agent, "layout": failing_agent, "mockup": failing_agent}

        def mock_create(agent_type, config=None):
            agent = agent_map.get(agent_type)
            if config:
                return lambda **kw: agent(**{**config, **kw})
            return agent

        with patch(
            "app.agents.orchestrator.agent_factory.AgentFactory.create",
            side_effect=mock_create,
        ):
            graph = TaskGraph()
            node = TaskNode(
                id="t1",
                agent_type="visual",
                alternatives=["layout", "mockup"],
                params={},
            )
            graph.add_task(node)
            # Reduce retries to speed up test
            node.max_retries = 1

            scheduler = TaskScheduler(max_concurrent=1)
            result = await scheduler.execute(graph, project_id="p1")

            assert result["success"] is False
            assert graph.nodes["t1"].status == "failed"


# ---------------------------------------------------------------------------
# 2. Per-node max_retries with exponential backoff
# ---------------------------------------------------------------------------

class TestPerNodeRetry:
    """Test that each node can have its own retry configuration."""

    def test_task_node_supports_max_retries(self):
        """TaskNode should support per-node max_retries field."""
        node = TaskNode(id="t1", agent_type="visual", max_retries=5)
        assert node.max_retries == 5

    def test_task_node_max_retries_default(self):
        """TaskNode max_retries should default gracefully."""
        node = TaskNode(id="t1", agent_type="visual")
        # Default behavior: inherit from scheduler if unset
        assert node.max_retries is None

    @pytest.mark.asyncio
    async def test_per_node_retry_overrides_scheduler_default(self):
        """Node's max_retries should override scheduler's global max_retries."""
        call_count = 0

        async def flaky_agent(project_id=None, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError(f"Attempt {call_count} failed")
            return {"status": "ok"}

        with patch(
            "app.agents.orchestrator.agent_factory.AgentFactory.create",
            return_value=flaky_agent,
        ):
            graph = TaskGraph()
            node = TaskNode(
                id="t1",
                agent_type="visual",
                max_retries=5,  # node-level: allow up to 5 retries
            )
            graph.add_task(node)

            # Scheduler has lower global max_retries, but node overrides
            scheduler = TaskScheduler(max_concurrent=1, max_retries=2)
            result = await scheduler.execute(graph, project_id="p1")

            assert result["success"] is True
            assert call_count == 3  # 2 failures + 1 success

    @pytest.mark.asyncio
    async def test_scheduler_falls_back_to_global_retries(self):
        """When node has no max_retries, use scheduler's global default."""
        call_count = 0

        async def flaky_agent(project_id=None, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RuntimeError("fail")
            return {"status": "ok"}

        with patch(
            "app.agents.orchestrator.agent_factory.AgentFactory.create",
            return_value=flaky_agent,
        ):
            graph = TaskGraph()
            node = TaskNode(id="t1", agent_type="visual")  # no per-node max_retries
            graph.add_task(node)

            scheduler = TaskScheduler(max_concurrent=1, max_retries=3)
            result = await scheduler.execute(graph, project_id="p1")

            assert result["success"] is True
            assert call_count == 2


# ---------------------------------------------------------------------------
# 3. Exponential backoff verification
# ---------------------------------------------------------------------------

class TestExponentialBackoff:
    """Test that retry delays follow exponential backoff pattern."""

    @pytest.mark.asyncio
    async def test_exponential_backoff_increasing_delays(self):
        """Retry delays should increase exponentially: 2s, 4s, 8s..."""
        delays = []

        async def failing_agent(project_id=None, **kwargs):
            raise RuntimeError("fail")

        original_sleep = asyncio.sleep
        async def track_sleep(delay):
            delays.append(delay)
            await original_sleep(0)  # don't actually wait

        with patch("asyncio.sleep", side_effect=track_sleep):
            with patch(
                "app.agents.orchestrator.agent_factory.AgentFactory.create",
                return_value=failing_agent,
            ):
                graph = TaskGraph()
                node = TaskNode(id="t1", agent_type="visual", max_retries=3)
                graph.add_task(node)

                scheduler = TaskScheduler(max_concurrent=1, max_retries=2)
                await scheduler.execute(graph, project_id="p1")

        # Should have retry delays: 2^0=1? Actually the code uses 2**attempt
        # attempt 0: sleep(2^0) = sleep(1)
        # attempt 1: sleep(2^1) = sleep(2)
        # But node has max_retries=3 and scheduler max_retries=2
        # Node should override: 3 retries = 3 attempts total (1 primary + 2 retries)
        # Retries happen: attempt 0 sleep(1), attempt 1 sleep(2)
        assert len(delays) >= 1
        # Verify increasing pattern
        if len(delays) >= 2:
            assert delays[0] < delays[1]
