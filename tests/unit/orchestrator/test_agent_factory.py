"""
TDD Step 1 (RED): 2 failing tests for AgentFactory.
"""
import pytest
from app.agents.orchestrator.agent_factory import AgentFactory


def test_factory_raises_on_unknown_type():
    """未知 agent_type 应抛出 ValueError。"""
    with pytest.raises(ValueError, match="Unknown agent type"):
        AgentFactory.create("nonexistent_agent", {})


def test_factory_create_returns_callable():
    """已知 agent_type 应返回可调用对象（agent 实例）。"""
    # 注册一个测试 agent 类型
    async def test_agent(project_id=None, **kwargs):
        return {"ok": True}

    AgentFactory.register("test_agent", test_agent)

    agent = AgentFactory.create("test_agent", {})
    assert callable(agent)
