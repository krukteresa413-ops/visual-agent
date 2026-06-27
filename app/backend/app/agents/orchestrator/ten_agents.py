"""十 Agent 的真实实现。

本文件先接入 6 个确定性 Agent(无需 LLM/网络):PM / Research / Brand /
Visual / Compliance / Export。LLM/渲染类(Copy / Image / Layout / Mockup)
后续接入;未接入者由编排核心(pipeline)自动标记 skipped。
"""
from __future__ import annotations

from typing import Dict

from app.agents.orchestrator.pipeline import Agent, PipelineContext


def _industry_key(brief: dict) -> str:
    return (brief.get("category") or "").strip() or "通用"


async def agent_pm(ctx: PipelineContext) -> dict:
    """Project Manager:拆解交付物与目标平台。"""
    b = ctx.brief
    deliverables = b.get("deliverables") or ["main_image", "selling_points", "scene_images"]
    platforms = b.get("target_platforms") or b.get("platforms") or []
    product = b.get("product_name") or (b.get("description") or "")[:40] or "未命名"
    return {"product": product, "deliverables": deliverables, "platforms": platforms}


async def agent_research(ctx: PipelineContext) -> dict:
    """Research:行业视觉关键词与场景洞察(模板)。"""
    from app.services.brand_strategy import BrandStrategyAgent
    ind = _industry_key(ctx.brief)
    kws = BrandStrategyAgent().generate_visual_keywords(ind) or []
    return {"industry": ind, "visual_keywords": kws}


async def agent_brand(ctx: PipelineContext) -> dict:
    """Brand:品牌策略(配色/调性/视觉风格,模板)。"""
    from app.services.brand_strategy import BrandStrategyAgent
    ind = _industry_key(ctx.brief)
    strat = BrandStrategyAgent().generate_strategy(
        industry=ind, product_name=ctx.brief.get("product_name", "产品")
    ) or {}
    return dict(strat)


async def agent_visual(ctx: PipelineContext) -> dict:
    """Visual:视觉方向(风格参数 + Moodboard)。"""
    from app.services.visual_direction import VisualDirection
    v = VisualDirection()
    sp = v.extract_style_params(ctx.brief)
    return {"style_params": sp, "moodboard": v.build_moodboard_context(sp)}


async def agent_compliance(ctx: PipelineContext) -> dict:
    """Compliance:广告法/平台合规检查(brief + 已生成文案)。"""
    from app.services.compliance import ComplianceChecker
    warnings = list(ComplianceChecker.check_brief(ctx.brief) or [])
    copy = ctx.results.get("copy") or {}
    text = " ".join(str(copy.get(k, "")) for k in ("headline", "body", "cta"))
    if text.strip():
        warnings += list(ComplianceChecker.check_text(text) or [])
    return {"warnings": warnings, "passed": len(warnings) == 0}


async def agent_export(ctx: PipelineContext) -> dict:
    """Export:汇总 brief/策略/资产为可归档导出包。"""
    from app.services.project_exporter import ProjectExporter
    r = ctx.results
    assets = []
    img = r.get("image") or {}
    if isinstance(img, dict) and img.get("url"):
        assets.append({"type": "main_image", "url": img["url"]})
    package = ProjectExporter().export({
        "name": ctx.brief.get("product_name", ""),
        "brief": ctx.brief,
        "strategy": r.get("brand", {}),
        "assets": assets,
    })
    return {"package": package, "asset_count": len(assets)}


_COPY_SYSTEM = (
    "你是中文营销文案专家。根据产品信息生成一组营销文案,返回纯 JSON(不要代码块):\n"
    '{"headline":"主标题","body":"正文(50字内)","cta":"行动号召"}\n'
    "要求:符合中国广告法,不使用极限词。"
)

# Image / Mockup 渲染的 provider 自动回退链(与 quick-generate 一致)
_IMAGE_CHAIN = ("dataeyes", "mige", "pollinations", "local")


async def _call_llm_resilient(system: str, user: str, *, temperature: float = 0.7,
                              max_tokens: int = 512, per_try_timeout: float = 22.0) -> dict:
    """主 provider(短超时)→ 备用 provider 回退;全失败返回 {}。

    避免单个 LLM 网关 503/挂死把 Agent 拖到超时。每次尝试用 wait_for 限时,
    取消底层(含其内部长重试)以快速失败。
    """
    import asyncio as _aio
    # 1) 当前激活 provider(默认 DeepSeek)
    try:
        from app.services.llm_client import LLMClient
        r = await _aio.wait_for(
            LLMClient().call(system_prompt=system, user_prompt=user, temperature=temperature, max_tokens=max_tokens),
            timeout=per_try_timeout,
        )
        if isinstance(r, dict) and r:
            return r
    except Exception:  # noqa: BLE001
        pass
    # 2) 备用 provider(OpenAI / gpt-4o),best-effort
    try:
        from app.services.llm_provider import OpenAIProvider
        r = await _aio.wait_for(
            OpenAIProvider().call(system_prompt=system, user_prompt=user, temperature=temperature, max_tokens=max_tokens),
            timeout=per_try_timeout,
        )
        if isinstance(r, dict) and r:
            return r
    except Exception:  # noqa: BLE001
        pass
    return {}


async def agent_copy(ctx: PipelineContext) -> dict:
    """Copy:中文营销文案(LLM + 重试/备用回退,网关不可用时降级为模板)。"""
    b = ctx.brief
    tone = (ctx.results.get("brand") or {}).get("tone_of_voice") or "专业可信"
    sp = "、".join(b.get("selling_points", []) or [])
    user = (
        f"产品:{b.get('product_name', '')}\n卖点:{sp}\n"
        f"品牌调性:{tone}\n描述:{b.get('description', '')}"
    )
    result = await _call_llm_resilient(_COPY_SYSTEM, user, max_tokens=512)
    if isinstance(result, dict) and (result.get("headline") or result.get("body")):
        return {"headline": result.get("headline", ""), "body": result.get("body", ""), "cta": result.get("cta", ""), "source": "llm"}
    # 降级:网关不可用时用模板,保证不空、不失败
    name = b.get("product_name") or "本产品"
    return {"headline": f"{name} 上新", "body": (sp or b.get("description", ""))[:50], "cta": "立即了解", "source": "fallback"}


async def agent_image(ctx: PipelineContext) -> dict:
    """Image:渲染主视觉(provider 自动回退)。"""
    from app.models.image_generation_model import ImageGenerationRequest
    from app.services.image_generation_service import image_generation_service
    b = ctx.brief
    moodboard = (ctx.results.get("visual") or {}).get("moodboard", "")
    sp = ", ".join(b.get("selling_points", []) or [])
    prompt = f"{b.get('product_name', '产品')} {sp}\n{moodboard}".strip()
    last_err = None
    for prov in _IMAGE_CHAIN:
        try:
            r = await image_generation_service.generate(ImageGenerationRequest(provider=prov, model=None, prompt=prompt, width=1024, height=1024))
            img = r.images[0] if getattr(r, "images", None) else None
            if img and img.url:
                return {"url": img.url, "provider": getattr(r, "provider", prov), "width": img.width, "height": img.height, "prompt": prompt}
        except Exception as e:  # noqa: BLE001 — 回退下一个 provider
            last_err = e
            continue
    raise RuntimeError(f"image agent 所有 provider 失败: {last_err}")


async def agent_layout(ctx: PipelineContext) -> dict:
    """Layout:中文排版布局(LLM,限时;网关不可用时降级为模板布局)。"""
    import asyncio as _aio
    from app.services.layout_agent import LayoutAgent
    b = ctx.brief
    asset_plan = {"main_image": ctx.results.get("image", {})}
    platform_id = (b.get("platforms") or b.get("target_platforms") or [None])[0]
    try:
        plan = await _aio.wait_for(LayoutAgent().generate_layout(
            project_id=ctx.project_id, brief=b, asset_plan=asset_plan,
            platform_id=platform_id, brand_context=(ctx.results.get("brand") or {}).get("visual_style"),
        ), timeout=25.0)
        out = plan.model_dump() if hasattr(plan, "model_dump") else dict(plan)
        out["source"] = "llm"
        return out
    except Exception:  # noqa: BLE001 — 降级为简单模板布局
        return {
            "source": "fallback",
            "sections": [
                {"type": "hero", "content": b.get("product_name", "")},
                {"type": "points", "content": b.get("selling_points", []) or []},
            ],
        }


async def agent_mockup(ctx: PipelineContext) -> dict:
    """Mockup:将主视觉套用到真实场景 mockup(渲染)。"""
    from app.services.mockup_agent import MockupAgent, MOCKUP_TYPES
    from app.models.image_generation_model import ImageGenerationRequest
    from app.services.image_generation_service import image_generation_service
    b = ctx.brief
    img = ctx.results.get("image") or {}
    mtype = MOCKUP_TYPES[0]["id"] if MOCKUP_TYPES else "phone"
    req = MockupAgent().build_request(mtype, b.get("product_name", "产品"), img.get("url"))
    url = None
    try:
        r = await image_generation_service.generate(ImageGenerationRequest(provider="dataeyes", model=None, prompt=req["prompt"], width=1024, height=1024))
        mi = r.images[0] if getattr(r, "images", None) else None
        url = mi.url if mi else None
    except Exception:  # noqa: BLE001 — mockup 渲染失败不致命,保留 request
        url = None
    return {"mockup_type": mtype, "request": req, "url": url}


def build_default_agents() -> Dict[str, Agent]:
    """全部 10 个真实 Agent。"""
    return {
        "pm": agent_pm,
        "research": agent_research,
        "brand": agent_brand,
        "copy": agent_copy,
        "visual": agent_visual,
        "image": agent_image,
        "layout": agent_layout,
        "mockup": agent_mockup,
        "compliance": agent_compliance,
        "export": agent_export,
    }
