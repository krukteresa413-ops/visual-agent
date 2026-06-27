"""TDD: 十 Agent 顺序编排核心(机制层,与具体 Agent 实现解耦)。"""
import pytest

from app.agents.orchestrator.pipeline import run_pipeline, AGENT_SEQUENCE

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
