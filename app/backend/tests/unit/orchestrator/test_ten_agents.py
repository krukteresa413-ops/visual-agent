"""TDD: 6 个确定性 Agent 的真实实现 + 与编排核心联跑。"""
import pytest

from app.agents.orchestrator.pipeline import PipelineContext, run_pipeline
from app.agents.orchestrator import ten_agents

BRIEF = {
    "product_name": "测试防晒衣",
    "category": "服饰",
    "selling_points": ["轻薄", "防晒"],
    "brand_style": "清爽/高级",
    "description": "女士防晒衣",
}


@pytest.mark.asyncio
async def test_deterministic_agents_return_structured_output():
    ctx = PipelineContext(brief=BRIEF, project_id=2)
    pm = await ten_agents.agent_pm(ctx)
    assert pm["product"] and isinstance(pm["deliverables"], list)
    res = await ten_agents.agent_research(ctx)
    assert "industry" in res and isinstance(res["visual_keywords"], list)
    br = await ten_agents.agent_brand(ctx)
    assert isinstance(br, dict)
    vis = await ten_agents.agent_visual(ctx)
    assert "primary_color" in vis["style_params"]
    comp = await ten_agents.agent_compliance(ctx)
    assert "warnings" in comp and isinstance(comp["warnings"], list)
    exp = await ten_agents.agent_export(ctx)
    assert "package" in exp and "asset_count" in exp


def test_build_default_has_the_six_real_agents():
    agents = ten_agents.build_default_agents()
    assert set(agents) == {"pm", "research", "brand", "visual", "compliance", "export"}


@pytest.mark.asyncio
async def test_pipeline_with_real_agents_six_success_four_skipped():
    result = await run_pipeline(BRIEF, project_id=2, agents=ten_agents.build_default_agents())
    statuses = {a["name"]: a["status"] for a in result["agents"]}
    assert statuses["PM"] == "success"
    assert statuses["Brand"] == "success"
    assert statuses["Export"] == "success"
    assert statuses["Image"] == "skipped"
    assert statuses["Copy"] == "skipped"
    # Export 能看到 Brand 的产物(上下文累积)
    assert "package" in result["results"]["export"]
