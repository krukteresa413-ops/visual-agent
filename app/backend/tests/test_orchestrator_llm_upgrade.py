"""十 Agent 含金量升级 —— 单元测试(不联网、不导入 main、不碰 DB)。

覆盖:
- dataeyes_text.extract_json 稳健性(围栏/夹带/垃圾/非对象)
- dataeyes_text.dataeyes_json 走 vision_service(成功/API 失败/异常)
- 三桩(brand/visual/research)LLM 成功 vs 模板降级
- copy 多版择优 / layout LLM 与降级
- image 两版并发 + vision 择优(winner A/B / 单版 / 全失败)
- quality_evaluator 走注入 client 的解析与降级
- run_pipeline 容错(单 Agent 失败不中断)

跑法(ECS venv,不重启后端):
  cd /opt/visual-agent/app/backend && .venv/bin/python -m pytest tests/test_orchestrator_llm_upgrade.py -q
"""
import asyncio

from app.services import dataeyes_text as dt
from app.agents.orchestrator import ten_agents as ta
from app.agents.orchestrator.pipeline import PipelineContext, run_pipeline
from app.services import quality_evaluator as qe


def run(coro):
    return asyncio.run(coro)


def _ctx(brief=None, results=None):
    c = PipelineContext(brief=brief or {"product_name": "测试产品", "category": "通用",
                                         "selling_points": ["卖点一", "卖点二"], "description": "一段描述"},
                        project_id=1)
    c.results = results or {}
    return c


# ── extract_json ────────────────────────────────────────────────────────
def test_extract_json_plain():
    assert dt.extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_fenced():
    assert dt.extract_json('```json\n{"a": 1, "b": "x"}\n```') == {"a": 1, "b": "x"}


def test_extract_json_embedded_prose():
    assert dt.extract_json('好的,结果如下:{"headline":"标题"} 以上。') == {"headline": "标题"}


def test_extract_json_nested_balanced():
    assert dt.extract_json('{"a": {"b": 1}, "c": [1,2]}') == {"a": {"b": 1}, "c": [1, 2]}


def test_extract_json_garbage_returns_empty():
    assert dt.extract_json("完全不是 json") == {}
    assert dt.extract_json("") == {}


def test_extract_json_non_object_returns_empty():
    # 顶层是数组 → 不是 dict → {}
    assert dt.extract_json("[1, 2, 3]") == {}


# ── dataeyes_json ──────────────────────────────────────────────────────
def test_dataeyes_json_success(monkeypatch):
    async def fake_analyze(images, prompt, max_tokens=512, temperature=0.3):
        assert images == []  # 空图=纯文字
        return {"success": True, "content": '```json\n{"ok": true}\n```'}
    monkeypatch.setattr("app.services.vision_service.vision_service.analyze", fake_analyze)
    assert run(dt.dataeyes_json("sys", "user")) == {"ok": True}


def test_dataeyes_json_api_failure(monkeypatch):
    async def fake_analyze(images, prompt, max_tokens=512, temperature=0.3):
        return {"success": False, "error": "402"}
    monkeypatch.setattr("app.services.vision_service.vision_service.analyze", fake_analyze)
    assert run(dt.dataeyes_json("sys", "user")) == {}


def test_dataeyes_json_exception(monkeypatch):
    async def fake_analyze(images, prompt, max_tokens=512, temperature=0.3):
        raise RuntimeError("network down")
    monkeypatch.setattr("app.services.vision_service.vision_service.analyze", fake_analyze)
    assert run(dt.dataeyes_json("sys", "user")) == {}


# ── brand / visual / research ──────────────────────────────────────────
def _patch_resilient(monkeypatch, fn):
    monkeypatch.setattr(ta, "_call_llm_resilient", fn)


def test_agent_brand_llm(monkeypatch):
    async def fake(system, user, **kw):
        return {"visual_style": "极简高级", "color_palette": ["#111", "#eee"],
                "tone_of_voice": "沉稳专业", "prompt_modifiers": "minimal, premium"}
    _patch_resilient(monkeypatch, fake)
    out = run(ta.agent_brand(_ctx()))
    assert out["source"] == "llm"
    assert out["visual_style"] == "极简高级"
    assert out["prompt_modifiers"] == "minimal, premium"


def test_agent_brand_fallback_generic(monkeypatch):
    # LLM 不可用 + "通用" 不在模板表 → 通用默认(非空),不再空产出
    async def fake(system, user, **kw):
        return {}
    _patch_resilient(monkeypatch, fake)
    out = run(ta.agent_brand(_ctx()))
    assert out["source"] == "fallback"
    assert out["visual_style"]           # 非空
    assert out["tone_of_voice"]


def test_agent_visual_llm_not_hardcoded_green(monkeypatch):
    async def fake(system, user, **kw):
        return {"primary_color": "#c0392b", "secondary_color": "#f9e79f",
                "style_keywords": ["复古", "暖调"], "typography": "serif",
                "composition": "rule-of-thirds", "moodboard": "暖调复古氛围"}
    _patch_resilient(monkeypatch, fake)
    out = run(ta.agent_visual(_ctx(results={"brand": {"visual_style": "复古"}})))
    assert out["source"] == "llm"
    assert out["style_params"]["primary_color"] == "#c0392b"   # 来自 LLM,非写死绿 #2d5a27
    assert out["moodboard"] == "暖调复古氛围"


def test_agent_visual_fallback(monkeypatch):
    async def fake(system, user, **kw):
        return {}
    _patch_resilient(monkeypatch, fake)
    out = run(ta.agent_visual(_ctx()))
    assert out["source"] == "fallback"
    assert out["style_params"]["primary_color"]      # 常量兜底仍有值
    assert out["moodboard"]


def test_agent_research_llm(monkeypatch):
    async def fake(system, user, **kw):
        return {"industry": "美妆", "visual_keywords": ["柔光", "细腻", "高级感"],
                "scene_insights": ["梳妆台场景"]}
    _patch_resilient(monkeypatch, fake)
    out = run(ta.agent_research(_ctx()))
    assert out["source"] == "llm"
    assert "柔光" in out["visual_keywords"]


def test_agent_research_fallback(monkeypatch):
    async def fake(system, user, **kw):
        return {}
    _patch_resilient(monkeypatch, fake)
    out = run(ta.agent_research(_ctx()))
    assert out["source"] == "fallback"
    assert isinstance(out["visual_keywords"], list)


# ── copy 多版择优 ────────────────────────────────────────────────────────
def test_agent_copy_variants_and_judge(monkeypatch):
    async def fake(system, user, **kw):
        if "3 组" in system:
            return {"variants": [{"headline": "H0", "body": "b0"},
                                  {"headline": "H1", "body": "b1"},
                                  {"headline": "H2", "body": "b2"}]}
        if "best_index" in system:
            return {"best_index": 2, "reason": "最佳"}
        return {}
    _patch_resilient(monkeypatch, fake)
    out = run(ta.agent_copy(_ctx()))
    assert out["source"] == "llm"
    assert out["chosen_index"] == 2
    assert out["headline"] == "H2"
    assert len(out["variants"]) == 3


def test_agent_copy_judge_out_of_range_defaults_zero(monkeypatch):
    async def fake(system, user, **kw):
        if "3 组" in system:
            return {"variants": [{"headline": "H0", "body": "b0"}, {"headline": "H1", "body": "b1"}]}
        if "best_index" in system:
            return {"best_index": 9}   # 越界 → 回退 0
        return {}
    _patch_resilient(monkeypatch, fake)
    out = run(ta.agent_copy(_ctx()))
    assert out["chosen_index"] == 0
    assert out["headline"] == "H0"


def test_agent_copy_fallback(monkeypatch):
    async def fake(system, user, **kw):
        return {}
    _patch_resilient(monkeypatch, fake)
    out = run(ta.agent_copy(_ctx()))
    assert out["source"] == "fallback"
    assert out["headline"]


# ── layout ───────────────────────────────────────────────────────────────
def test_agent_layout_llm(monkeypatch):
    async def fake(system, user, **kw):
        return {"sections": [{"type": "hero", "title": "主区"}], "layout_note": "留白"}
    _patch_resilient(monkeypatch, fake)
    out = run(ta.agent_layout(_ctx(results={"copy": {"headline": "标题"}})))
    assert out["source"] == "llm"
    assert out["sections"][0]["type"] == "hero"


def test_agent_layout_fallback(monkeypatch):
    async def fake(system, user, **kw):
        return {}
    _patch_resilient(monkeypatch, fake)
    out = run(ta.agent_layout(_ctx()))
    assert out["source"] == "fallback"
    assert out["sections"]


# ── image 两版并发 + 择优 ────────────────────────────────────────────────
class _FakeImg:
    def __init__(self, url):
        self.url, self.width, self.height = url, 1024, 1024


class _FakeRes:
    def __init__(self, url):
        self.images, self.provider = [_FakeImg(url)], "dataeyes"


def _patch_image(monkeypatch, gen_fn, cmp_fn=None):
    monkeypatch.setattr("app.services.image_generation_service.image_generation_service.generate", gen_fn)
    if cmp_fn is not None:
        monkeypatch.setattr("app.services.vision_service.vision_service.compare_images", cmp_fn)


def test_agent_image_two_variants_winner_b(monkeypatch):
    async def gen(req):
        # 第二版 prompt 更长 → url 不同,便于区分
        return _FakeRes(f"http://img/{len(req.prompt)}")

    async def cmp(a, b, criteria=""):
        return {"winner": "B", "scores": {"A": 70, "B": 90}}
    _patch_image(monkeypatch, gen, cmp)
    out = run(ta.agent_image(_ctx(results={"visual": {"moodboard": "mb"}, "brand": {"prompt_modifiers": "m"}})))
    assert out["variant_count"] == 2
    assert len(out["variant_urls"]) == 2
    assert out["url"] == out["variant_urls"][1]      # 选了 B


def test_agent_image_winner_a(monkeypatch):
    async def gen(req):
        return _FakeRes(f"http://img/{len(req.prompt)}")

    async def cmp(a, b, criteria=""):
        return {"winner": "A"}
    _patch_image(monkeypatch, gen, cmp)
    out = run(ta.agent_image(_ctx(results={"visual": {"moodboard": "mb"}})))
    assert out["url"] == out["variant_urls"][0]      # 选了 A


def test_agent_image_single_variant(monkeypatch):
    async def gen(req):
        if "换一种" in req.prompt:      # 第二版全 provider 失败
            raise RuntimeError("fail")
        return _FakeRes("http://img/base")
    _patch_image(monkeypatch, gen)
    out = run(ta.agent_image(_ctx()))
    assert out["variant_count"] == 1
    assert out["url"] == "http://img/base"


def test_agent_image_all_fail_raises(monkeypatch):
    async def gen(req):
        raise RuntimeError("provider down")
    _patch_image(monkeypatch, gen)
    try:
        run(ta.agent_image(_ctx()))
        assert False, "应抛 RuntimeError"
    except RuntimeError:
        pass


# ── quality_evaluator ──────────────────────────────────────────────────
class _FakeClient:
    def __init__(self, raw=None, exc=None):
        self._raw, self._exc = raw, exc
        self._provider = type("P", (), {"_model": "fake"})()

    async def call(self, system_prompt, user_prompt, temperature=0.3, max_tokens=1024):
        if self._exc:
            raise self._exc
        return self._raw


def test_quality_evaluator_parse():
    raw = {"dimensions": [{"name": "composition", "name_cn": "构图", "score": 8, "reasoning": "好"}],
           "overall_score": 8, "summary": "不错"}
    rep = run(qe.evaluate_assets({"product_name": "P"}, {"main_image": {}}, llm_client=_FakeClient(raw=raw)))
    assert rep.overall_score == 8
    assert rep.dimensions[0].score == 8


def test_quality_evaluator_fallback_on_error():
    rep = run(qe.evaluate_assets({"product_name": "P"}, {}, llm_client=_FakeClient(exc=RuntimeError("boom"))))
    assert rep.overall_score == 6      # 兜底报告
    assert len(rep.dimensions) == 3


# ── pipeline 容错 ──────────────────────────────────────────────────────
def test_run_pipeline_fault_tolerant():
    async def ok(ctx):
        return {"ok": True}

    async def boom(ctx):
        raise RuntimeError("agent 炸了")
    # 只放两个 key(其余序列项无对应 agent → skipped),其中 image 失败
    registry = {"pm": ok, "image": boom}
    out = run(run_pipeline({"product_name": "P"}, 1, agents=registry))
    by_key = {a["key"]: a["status"] for a in out["agents"]}
    assert by_key["pm"] == "success"
    assert by_key["image"] == "failed"      # 失败被标记
    assert by_key["copy"] == "skipped"      # 未提供 → skipped,不中断
    assert out["results"]["pm"] == {"ok": True}
