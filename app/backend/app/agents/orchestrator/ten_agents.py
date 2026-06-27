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


def build_default_agents() -> Dict[str, Agent]:
    """已接入的真实 Agent。未列出的(copy/image/layout/mockup)由 pipeline 标 skipped。"""
    return {
        "pm": agent_pm,
        "research": agent_research,
        "brand": agent_brand,
        "visual": agent_visual,
        "compliance": agent_compliance,
        "export": agent_export,
    }
