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


_RESEARCH_SYSTEM = (
    "你是电商视觉调研专家。基于产品与行业,输出该产品专属的视觉调研,返回纯 JSON:\n"
    '{"industry":"行业","visual_keywords":["关键词",...5-8个],"scene_insights":["场景/氛围洞察",...2-4条]}\n'
    "关键词要具体、可直接用于出图(风格/材质/光影/构图),避免空泛套话。"
)
_BRAND_SYSTEM = (
    "你是资深品牌视觉策略师。基于产品信息,输出该产品专属的品牌视觉策略,返回纯 JSON:\n"
    '{"visual_style":"视觉风格","color_palette":["#hex",...],"tone_of_voice":"文案调性",'
    '"forbidden_elements":["规避元素",...],"prompt_modifiers":"英文出图风格修饰词"}\n'
    "配色与风格要贴合产品本身与目标人群,避免套话。"
)
_VISUAL_SYSTEM = (
    "你是视觉设计总监。基于产品与品牌策略,给出该产品专属的视觉方向,返回纯 JSON:\n"
    '{"primary_color":"#hex","secondary_color":"#hex","style_keywords":["风格词",...],'
    '"typography":"serif|sans-serif|display","composition":"构图方式","moodboard":"一段中文氛围描述,用于出图"}\n'
    "配色/风格必须由该产品本身推导,不要套用固定色。"
)


async def agent_research(ctx: PipelineContext) -> dict:
    """Research:行业视觉关键词与场景洞察(LLM;不可用时回退模板)。"""
    b = ctx.brief
    ind = _industry_key(b)
    user = (
        f"产品:{b.get('product_name','')}\n品类:{ind}\n"
        f"卖点:{'、'.join(b.get('selling_points', []) or [])}\n描述:{b.get('description','')}"
    )
    llm = await _call_llm_resilient(_RESEARCH_SYSTEM, user, max_tokens=500, temperature=0.7)
    kws = llm.get("visual_keywords") if isinstance(llm, dict) else None
    if kws:
        return {"industry": llm.get("industry") or ind, "visual_keywords": kws,
                "scene_insights": llm.get("scene_insights") or [], "source": "llm"}
    # 降级:模板关键词(命中行业才有,否则空)
    from app.services.brand_strategy import BrandStrategyAgent
    tkws = BrandStrategyAgent().generate_visual_keywords(ind) or []
    return {"industry": ind, "visual_keywords": tkws, "source": "fallback"}


async def agent_brand(ctx: PipelineContext) -> dict:
    """Brand:品牌策略(LLM 产出产品专属策略;不可用时回退模板→通用默认)。"""
    b = ctx.brief
    ind = _industry_key(b)
    user = (
        f"产品:{b.get('product_name','')}\n品类:{ind}\n"
        f"卖点:{'、'.join(b.get('selling_points', []) or [])}\n"
        f"目标市场:{'、'.join(b.get('target_market', []) or [])}\n描述:{b.get('description','')}"
    )
    llm = await _call_llm_resilient(_BRAND_SYSTEM, user, max_tokens=600, temperature=0.6)
    if isinstance(llm, dict) and (llm.get("visual_style") or llm.get("tone_of_voice")):
        llm["source"] = "llm"
        return llm
    # 降级:原行业模板;模板也命不中时给通用默认(根治"通用"空产出)
    from app.services.brand_strategy import BrandStrategyAgent
    strat = BrandStrategyAgent().generate_strategy(
        industry=ind, product_name=b.get("product_name", "产品")
    ) or {}
    if not strat:
        strat = {"visual_style": "简约现代", "color_palette": ["#2d2d2d", "#f5f5f5"],
                 "tone_of_voice": "专业可信", "forbidden_elements": []}
    strat = dict(strat)
    strat["source"] = "fallback"
    return strat


async def agent_visual(ctx: PipelineContext) -> dict:
    """Visual:视觉方向(LLM 从 brief+brand 推导;不可用时回退常量)。"""
    b = ctx.brief
    brand = ctx.results.get("brand") or {}
    user = (
        f"产品:{b.get('product_name','')}\n"
        f"品牌视觉风格:{brand.get('visual_style','')}\n"
        f"配色参考:{brand.get('color_palette','')}\n"
        f"卖点:{'、'.join(b.get('selling_points', []) or [])}\n描述:{b.get('description','')}"
    )
    llm = await _call_llm_resilient(_VISUAL_SYSTEM, user, max_tokens=500, temperature=0.6)
    if isinstance(llm, dict) and llm.get("primary_color"):
        style_params = {
            "primary_color": llm.get("primary_color"),
            "secondary_color": llm.get("secondary_color"),
            "style_keywords": llm.get("style_keywords") or [],
            "typography": llm.get("typography") or "sans-serif",
            "composition": llm.get("composition") or "balanced",
        }
        moodboard = llm.get("moodboard") or (
            f"配色:{style_params['primary_color']}/{style_params.get('secondary_color') or ''}; "
            f"风格:{'、'.join(style_params['style_keywords'])}; 构图:{style_params['composition']}"
        )
        return {"style_params": style_params, "moodboard": moodboard, "source": "llm"}
    # 降级:原常量实现
    from app.services.visual_direction import VisualDirection
    v = VisualDirection()
    sp = v.extract_style_params(b)
    return {"style_params": sp, "moodboard": v.build_moodboard_context(sp), "source": "fallback"}


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


_COPY_SYSTEM_VARIANTS = (
    "你是中文营销文案专家。根据产品信息生成 3 组风格各异的营销文案,返回纯 JSON:\n"
    '{"variants":[{"headline":"主标题","body":"正文(50字内)","cta":"行动号召","angle":"卖点角度"}, ...]}\n'
    "3 组角度要不同(如:功能卖点 / 情感共鸣 / 场景化)。符合中国广告法,不使用极限词。"
)
_COPY_JUDGE_SYSTEM = (
    "你是资深营销总监。从候选文案中选出最适合该产品的一组,只输出 JSON:\n"
    '{"best_index":0,"reason":"一句话理由"}'
)

# Image / Mockup 渲染的 provider 自动回退链(与 quick-generate 一致)
_IMAGE_CHAIN = ("dataeyes", "mige", "pollinations", "local")


async def _call_llm_resilient(system: str, user: str, *, temperature: float = 0.7,
                              max_tokens: int = 512, per_try_timeout: float = 30.0) -> dict:
    """出 JSON。DataEyes(唯一可用文字通道)优先 → 旧链路兜底 → {}。

    第一性原理:llm_provider 注册的 Zydmx/DeepSeek 当前均失效,旧两腿基本必死;
    DataEyes(gpt-4o /responses)是唯一活着的文字 LLM,故置为首选。旧链路保留,
    以便其恢复后自动复用。每次尝试用 wait_for 限时以快速失败。全失败返回 {},
    交由各 Agent 降级为模板(绝不中断流水线)。
    """
    import asyncio as _aio
    # 旧链路已知失效,仅"以防恢复"保留 → 短超时快速失败,避免 DataEyes 也挂时
    # 每个 Agent 在死 provider 上白等 per_try_timeout(否则全流水线拖到数分钟)。
    _fallback_timeout = min(per_try_timeout, 8.0)
    # 1) DataEyes 优先(唯一稳定的文字通道),给足 per_try_timeout
    try:
        from app.services.dataeyes_text import dataeyes_json
        r = await dataeyes_json(system, user, max_tokens=max_tokens,
                                temperature=temperature, per_try_timeout=per_try_timeout)
        if isinstance(r, dict) and r:
            return r
    except Exception:  # noqa: BLE001
        pass
    # 2) 旧链路兜底: 当前激活 provider(默认 DeepSeek),短超时
    try:
        from app.services.llm_client import LLMClient
        r = await _aio.wait_for(
            LLMClient().call(system_prompt=system, user_prompt=user, temperature=temperature, max_tokens=max_tokens),
            timeout=_fallback_timeout,
        )
        if isinstance(r, dict) and r:
            return r
    except Exception:  # noqa: BLE001
        pass
    # 3) 旧链路兜底: 备用 provider(OpenAI / gpt-4o),短超时 best-effort
    try:
        from app.services.llm_provider import OpenAIProvider
        r = await _aio.wait_for(
            OpenAIProvider().call(system_prompt=system, user_prompt=user, temperature=temperature, max_tokens=max_tokens),
            timeout=_fallback_timeout,
        )
        if isinstance(r, dict) and r:
            return r
    except Exception:  # noqa: BLE001
        pass
    return {}


async def agent_copy(ctx: PipelineContext) -> dict:
    """Copy:中文营销文案 —— 多版生成 + 择优(LLM;不可用时降级为模板)。"""
    b = ctx.brief
    tone = (ctx.results.get("brand") or {}).get("tone_of_voice") or "专业可信"
    sp = "、".join(b.get("selling_points", []) or [])
    user = (
        f"产品:{b.get('product_name', '')}\n卖点:{sp}\n"
        f"品牌调性:{tone}\n描述:{b.get('description', '')}"
    )
    # 1) 生成多版文案
    result = await _call_llm_resilient(_COPY_SYSTEM_VARIANTS, user, max_tokens=800, temperature=0.85)
    variants = result.get("variants") if isinstance(result, dict) else None
    variants = [v for v in (variants or []) if isinstance(v, dict) and (v.get("headline") or v.get("body"))]
    if variants:
        chosen_index = 0
        # 2) 多版时择优(judge 失败则用第 0 版)
        if len(variants) > 1:
            listing = "\n".join(
                f"[{i}] {v.get('headline', '')} / {v.get('body', '')}" for i, v in enumerate(variants)
            )
            judge = await _call_llm_resilient(
                _COPY_JUDGE_SYSTEM, f"产品:{b.get('product_name', '')}\n候选:\n{listing}",
                max_tokens=120, temperature=0.2,
            )
            idx = judge.get("best_index") if isinstance(judge, dict) else None
            if isinstance(idx, int) and 0 <= idx < len(variants):
                chosen_index = idx
        best = variants[chosen_index]
        return {"headline": best.get("headline", ""), "body": best.get("body", ""),
                "cta": best.get("cta", ""), "source": "llm",
                "variants": variants, "chosen_index": chosen_index}
    # 降级:网关不可用时用模板,保证不空、不失败
    name = b.get("product_name") or "本产品"
    return {"headline": f"{name} 上新", "body": (sp or b.get("description", ""))[:50],
            "cta": "立即了解", "source": "fallback"}


async def agent_image(ctx: PipelineContext) -> dict:
    """Image:渲染主视觉 —— 两版并发生成 + vision 择优(降级为单版/provider 回退)。"""
    import asyncio as _aio
    from app.models.image_generation_model import ImageGenerationRequest
    from app.services.image_generation_service import image_generation_service
    b = ctx.brief
    visual = ctx.results.get("visual") or {}
    moodboard = visual.get("moodboard", "")
    modifiers = (ctx.results.get("brand") or {}).get("prompt_modifiers", "") or ""
    sp = ", ".join(b.get("selling_points", []) or [])
    base = f"{b.get('product_name', '产品')} {sp}\n{moodboard}\n{modifiers}".strip()
    prompts = [base, f"{base}\n换一种构图与镜头视角,强调产品细节与质感"]

    async def _gen(prompt: str):
        last_err = None
        for prov in _IMAGE_CHAIN:
            try:
                r = await image_generation_service.generate(ImageGenerationRequest(
                    provider=prov, model=None, prompt=prompt, width=1024, height=1024))
                img = r.images[0] if getattr(r, "images", None) else None
                if img and img.url:
                    return {"url": img.url, "provider": getattr(r, "provider", prov),
                            "width": img.width, "height": img.height, "prompt": prompt}
            except Exception as e:  # noqa: BLE001 — 回退下一个 provider
                last_err = e
                continue
        return None

    results = await _aio.gather(*[_gen(p) for p in prompts], return_exceptions=True)
    cands = [r for r in results if isinstance(r, dict) and r.get("url")]
    if not cands:
        raise RuntimeError("image agent 所有 provider 失败(两版均未产出)")
    if len(cands) == 1:
        return {**cands[0], "variant_count": 1}
    # 两版择优:vision 比较,失败则保留第一版
    chosen = cands[0]
    try:
        from app.services.vision_service import vision_service
        cmp = await _aio.wait_for(
            vision_service.compare_images(
                cands[0]["url"], cands[1]["url"],
                criteria=f"{b.get('product_name', '')} 商业主视觉;风格:{moodboard[:60]}"),
            timeout=20.0)
        if isinstance(cmp, dict) and cmp.get("winner") == "B":
            chosen = cands[1]
    except Exception:  # noqa: BLE001 — 比较不可用则保留第一版
        pass
    return {**chosen, "variant_count": len(cands), "variant_urls": [c["url"] for c in cands]}


_LAYOUT_SYSTEM = (
    "你是电商视觉排版专家。根据产品、主标题与目标平台,给出中文详情页/主图排版方案,返回纯 JSON:\n"
    '{"sections":[{"type":"hero|points|scene|cta","title":"...","content":"..."}],"layout_note":"排版要点"}'
)


async def agent_layout(ctx: PipelineContext) -> dict:
    """Layout:中文排版(LLM 走 DataEyes;不可用时降级为简单模板布局)。"""
    b = ctx.brief
    copy = ctx.results.get("copy") or {}
    platform = (b.get("platforms") or b.get("target_platforms") or ["通用"])[0]
    user = (
        f"产品:{b.get('product_name', '')}\n"
        f"卖点:{'、'.join(b.get('selling_points', []) or [])}\n"
        f"主标题:{copy.get('headline', '')}\n目标平台:{platform}"
    )
    llm = await _call_llm_resilient(_LAYOUT_SYSTEM, user, max_tokens=600, temperature=0.5)
    if isinstance(llm, dict) and llm.get("sections"):
        llm["source"] = "llm"
        return llm
    # 降级:简单模板布局
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
