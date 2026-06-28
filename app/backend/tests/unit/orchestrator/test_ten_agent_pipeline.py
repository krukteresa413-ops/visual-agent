"""TDD: 十 Agent 顺序编排核心(机制层,与具体 Agent 实现解耦)。"""
import pytest

from app.agents.orchestrator.pipeline import run_pipeline, AGENT_SEQUENCE, build_generation_result

EXPECTED_KEYS = ["pm", "research", "brand", "copy", "visual", "image", "layout", "mockup", "compliance", "export"]
EXPECTED_NAMES = ["PM", "Research", "Brand", "Copy", "Visual", "Image", "Layout", "Mockup", "Compliance", "Export"]


def test_sequence_is_the_ten_named_agents():
    assert [k for k, _ in AGENT_SEQUENCE] == EXPECTED_KEYS
    assert [n for _, n in AGENT_SEQUENCE] == EXPECTED_NAMES


@pytest.mark.asyncio
async def test_runs_all_ten_in_order_with_progress_and_context():
    calls = []
    events = []

    def make(key):
        async def agent(ctx):
            calls.append(key)
            return {"key": key, "saw": list(ctx.results.keys())}
        return agent

    agents = {k: make(k) for k, _ in AGENT_SEQUENCE}

    async def progress(label, status, message=""):
        events.append((label, status))

    result = await run_pipeline({"product_name": "X"}, project_id=2, progress_callback=progress, agents=agents)

    # 顺序
    assert calls == EXPECTED_KEYS
    # 上下文累积:最后一个 Agent 能看到前面所有 Agent 的产物
    assert result["results"]["export"]["saw"] == EXPECTED_KEYS[:-1]
    # 每个 Agent 都 emit 了 running(按名顺序)
    running = [lbl for lbl, st in events if st == "running"]
    assert running == EXPECTED_NAMES
    # 每个 Agent 状态 success,且名字顺序正确
    assert [a["status"] for a in result["agents"]] == ["success"] * 10
    assert [a["name"] for a in result["agents"]] == EXPECTED_NAMES


@pytest.mark.asyncio
async def test_failed_agent_is_marked_and_pipeline_continues():
    async def ok(ctx):
        return {"ok": True}

    async def boom(ctx):
        raise RuntimeError("agent boom")

    agents = {k: (boom if k == "copy" else ok) for k, _ in AGENT_SEQUENCE}
    events = []

    async def progress(label, status, message=""):
        events.append((label, status))

    result = await run_pipeline({}, 2, progress_callback=progress, agents=agents)
    statuses = {a["name"]: a["status"] for a in result["agents"]}
    assert statuses["Copy"] == "failed"
    assert statuses["Export"] == "success"  # 失败后继续跑后续 Agent
    assert ("Copy", "failed") in events


@pytest.mark.asyncio
async def test_per_agent_completion_uses_success_not_done():
    """单 Agent 完成用 status='success';绝不能用 'done'(会让 SSE 把整条流提前关闭)。"""
    async def ok(ctx):
        return {"ok": True}

    agents = {k: ok for k, _ in AGENT_SEQUENCE}
    events = []

    async def progress(label, status, message=""):
        events.append((label, status))

    await run_pipeline({}, 2, progress_callback=progress, agents=agents)
    assert ("PM", "success") in events
    assert all(s != "done" for _, s in events)


@pytest.mark.asyncio
async def test_slow_agent_times_out_and_pipeline_continues():
    import asyncio

    async def slow(ctx):
        await asyncio.sleep(5)
        return {}

    async def ok(ctx):
        return {"ok": True}

    agents = {k: (slow if k == "layout" else ok) for k, _ in AGENT_SEQUENCE}
    events = []

    async def progress(label, status, message=""):
        events.append((label, status))

    result = await run_pipeline({}, 2, progress_callback=progress, agents=agents, timeout_seconds=0.05)
    statuses = {a["name"]: a["status"] for a in result["agents"]}
    assert statuses["Layout"] == "failed"  # 超时被标失败
    assert statuses["Export"] == "success"  # 超时后继续
    assert ("Layout", "failed") in events


@pytest.mark.asyncio
async def test_missing_agent_is_skipped_not_crash():
    async def ok(ctx):
        return {"ok": True}

    # 只注册一半,其余应标 skipped 而不是崩
    agents = {k: ok for k in ["pm", "research", "brand"]}
    result = await run_pipeline({}, 2, agents=agents)
    statuses = {a["name"]: a["status"] for a in result["agents"]}
    assert statuses["PM"] == "success"
    assert statuses["Mockup"] == "skipped"
    assert len(result["agents"]) == 10


def test_build_generation_result_maps_assets():
    results = {
        "image": {"url": "/uploads/a.png", "width": 1024, "height": 1024, "provider": "dataeyes"},
        "mockup": {"url": "/uploads/m.png"},
        "copy": {"headline": "标题", "body": "正文", "cta": "立即购买"},
    }
    gen = build_generation_result({"product_name": "X"}, results)
    assert gen["main_image"]["url"] == "/uploads/a.png"
    assert gen["scene_images"][0]["url"] == "/uploads/m.png"
    assert gen["selling_points"][0]["point"] == "标题"
    assert gen["ad_material"]["cta"] == "立即购买"


def test_build_generation_result_handles_empty():
    gen = build_generation_result({}, {})
    assert gen["main_image"] is None
    assert gen["scene_images"] == []


def test_summarize_produces_real_conclusions():
    from app.agents.orchestrator.pipeline import _summarize
    assert "空山新品" in _summarize("copy", {"headline": "空山新品"})
    assert "降级" in _summarize("copy", {"headline": "X", "source": "fallback"})
    assert "provider" in _summarize("image", {"url": "/x.png", "provider": "dataeyes"})
    assert _summarize("compliance", {"passed": True}) == "合规检查通过"
    assert _summarize("unknown", {}) == "已完成"
