"""十 Agent 顺序编排核心。

机制层:按固定顺序运行 10 个具名 Agent,每个 Agent 共享累积上下文(brief +
前序 Agent 产物),逐个上报进度;单个 Agent 失败标记后继续,不中断整条流水线。
具体 Agent 实现见 ten_agents.py(通过 agents 注入或默认注册表)。
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Dict, Optional

# 固定编排顺序(下游 Agent 依赖上游产物)
AGENT_SEQUENCE = [
    ("pm", "PM"),
    ("research", "Research"),
    ("brand", "Brand"),
    ("copy", "Copy"),
    ("visual", "Visual"),
    ("image", "Image"),
    ("layout", "Layout"),
    ("mockup", "Mockup"),
    ("compliance", "Compliance"),
    ("export", "Export"),
]

# Agent 签名:async (ctx) -> dict
Agent = Callable[["PipelineContext"], Awaitable[dict]]
ProgressCallback = Callable[[str, str, str], Awaitable[None]]


@dataclass
class PipelineContext:
    brief: dict
    project_id: int
    results: Dict[str, dict] = field(default_factory=dict)


async def _noop_progress(label: str, status: str, message: str = "") -> None:
    return None


async def run_pipeline(
    brief: dict,
    project_id: int,
    progress_callback: Optional[ProgressCallback] = None,
    agents: Optional[Dict[str, Agent]] = None,
    timeout_seconds: float = 90.0,
) -> dict:
    """顺序运行十 Agent。返回 {"agents": [{key,name,status,error?}], "results": {key: output}}。

    单个 Agent 失败或超时(timeout_seconds)只标记该 Agent,不中断整条流水线,避免某个
    挂死的 LLM/渲染调用拖垮全流程。
    """
    progress = progress_callback or _noop_progress
    registry = agents if agents is not None else _default_agents()
    ctx = PipelineContext(brief=brief or {}, project_id=project_id)
    summary: list[dict] = []

    for key, name in AGENT_SEQUENCE:
        agent = registry.get(key)
        if agent is None:
            summary.append({"key": key, "name": name, "status": "skipped"})
            await progress(name, "skipped", "未启用")
            continue
        await progress(name, "running", f"{name} 处理中…")
        try:
            output = await asyncio.wait_for(agent(ctx), timeout=timeout_seconds)
            ctx.results[key] = output if isinstance(output, dict) else {"output": output}
            summary.append({"key": key, "name": name, "status": "success"})
            # 用 "success"(非 "done")上报单 Agent 完成:避免 GenerationTracker SSE
            # 把单 Agent 的 done 当成整体终止而提前关闭流(导致进度卡在第一个 Agent)。
            await progress(name, "success", "")
        except asyncio.TimeoutError:
            msg = f"超时(>{int(timeout_seconds)}s)"
            summary.append({"key": key, "name": name, "status": "failed", "error": msg})
            await progress(name, "failed", msg)
        except Exception as e:  # noqa: BLE001 — 单 Agent 失败不应中断整条流水线
            summary.append({"key": key, "name": name, "status": "failed", "error": str(e)[:200]})
            await progress(name, "failed", str(e)[:120])

    return {"agents": summary, "results": ctx.results}


def build_generation_result(brief: dict, results: Dict[str, dict]) -> dict:
    """把十 Agent 编排产物映射成画布可用的 gen_result(与 quick-generate 同结构)。"""
    img = results.get("image") or {}
    mockup = results.get("mockup") or {}
    copy = results.get("copy") or {}

    main_image = None
    if img.get("url"):
        main_image = {
            "asset_type": "main_image",
            "url": img["url"],
            "thumbnail_url": img["url"],
            "width": img.get("width"),
            "height": img.get("height"),
            "model": img.get("provider"),
            "goal": (brief or {}).get("product_name", ""),
            "status": "succeeded",
        }

    scene_images = []
    if mockup.get("url"):
        scene_images.append({
            "asset_type": "scene_image",
            "url": mockup["url"],
            "thumbnail_url": mockup["url"],
            "goal": "mockup",
            "status": "succeeded",
        })

    selling_points = []
    if copy.get("headline") or copy.get("body"):
        selling_points.append({"point": copy.get("headline", ""), "description": copy.get("body", "")})

    return {
        "main_image": main_image,
        "white_bg": None,
        "scene_images": scene_images,
        "selling_points": selling_points,
        "video_scripts": [],
        "ad_material": {"hook": copy.get("headline", ""), "cta": copy.get("cta", "")},
    }


def _default_agents() -> Dict[str, Agent]:
    """默认真实 Agent 注册表(迭代 2 接入)。当前为空 → 真实调用时全部 skipped。"""
    try:
        from app.agents.orchestrator.ten_agents import build_default_agents
        return build_default_agents()
    except Exception:
        return {}
