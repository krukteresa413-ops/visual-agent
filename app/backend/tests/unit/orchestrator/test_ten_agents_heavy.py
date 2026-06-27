"""TDD: 4 个重型 Agent(Copy/Image/Layout/Mockup)的真实接线(mock 掉 LLM/渲染)。"""
import pytest

from app.agents.orchestrator.pipeline import PipelineContext
from app.agents.orchestrator import ten_agents

BRIEF = {"product_name": "测试", "category": "服饰", "selling_points": ["轻薄"], "brand_style": "清爽"}


def _ctx():
    return PipelineContext(brief=BRIEF, project_id=2)


@pytest.mark.asyncio
async def test_copy_uses_llm(monkeypatch):
    from app.services import llm_client

    async def fake_call(self, system_prompt, user_prompt, **kw):
        return {"headline": "H", "body": "B", "cta": "C"}

    monkeypatch.setattr(llm_client.LLMClient, "call", fake_call)
    out = await ten_agents.agent_copy(_ctx())
    assert out["headline"] == "H" and out["body"] == "B" and out["cta"] == "C"
    assert out["source"] == "llm"


@pytest.mark.asyncio
async def test_copy_degrades_to_template_when_llm_unavailable(monkeypatch):
    async def fake_resilient(*a, **k):
        return {}
    monkeypatch.setattr(ten_agents, "_call_llm_resilient", fake_resilient)
    out = await ten_agents.agent_copy(_ctx())
    assert out["source"] == "fallback"
    assert out["headline"]  # 降级也保证非空


@pytest.mark.asyncio
async def test_image_returns_url_and_falls_back(monkeypatch):
    from app.services import image_generation_service as igs

    class FakeImg:
        url = "/uploads/x.png"
        width = 1024
        height = 1024

    class FakeResult:
        images = [FakeImg()]
        provider = "pollinations"

    calls = []

    async def fake_generate(request):
        calls.append(request.provider)
        if request.provider in ("dataeyes", "mige"):
            raise RuntimeError("provider down")
        return FakeResult()

    monkeypatch.setattr(igs.image_generation_service, "generate", fake_generate)
    out = await ten_agents.agent_image(_ctx())
    assert out["url"] == "/uploads/x.png"
    assert calls[:3] == ["dataeyes", "mige", "pollinations"]  # 真发生了回退


@pytest.mark.asyncio
async def test_layout_returns_dict(monkeypatch):
    from app.services import layout_agent as la

    class FakePlan:
        def model_dump(self):
            return {"sections": []}

    async def fake_layout(self, **kw):
        return FakePlan()

    monkeypatch.setattr(la.LayoutAgent, "generate_layout", fake_layout)
    out = await ten_agents.agent_layout(_ctx())
    assert out["sections"] == [] and out["source"] == "llm"


@pytest.mark.asyncio
async def test_layout_degrades_to_template_on_failure(monkeypatch):
    from app.services import layout_agent as la

    async def boom(self, **kw):
        raise RuntimeError("gateway down")

    monkeypatch.setattr(la.LayoutAgent, "generate_layout", boom)
    out = await ten_agents.agent_layout(_ctx())
    assert out["source"] == "fallback"
    assert out["sections"]


@pytest.mark.asyncio
async def test_mockup_builds_request_and_renders(monkeypatch):
    from app.services import image_generation_service as igs

    class FakeImg:
        url = "/uploads/m.png"
        width = 1024
        height = 1024

    class FakeResult:
        images = [FakeImg()]
        provider = "dataeyes"

    async def fake_generate(request):
        return FakeResult()

    monkeypatch.setattr(igs.image_generation_service, "generate", fake_generate)
    out = await ten_agents.agent_mockup(_ctx())
    assert out["mockup_type"]
    assert "request" in out and "prompt" in out["request"]
    assert out["url"] == "/uploads/m.png"


def test_build_default_now_has_all_ten():
    assert set(ten_agents.build_default_agents()) == {
        "pm", "research", "brand", "copy", "visual", "image", "layout", "mockup", "compliance", "export",
    }
