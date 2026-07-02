import asyncio
import hashlib
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, get_db
from app.db.crud_visual_asset_v2 import save_asset_plan
from app.models.auth import User
from app.services.auth_service import get_current_user
from app.services.canvas_service import assert_generation_access
from app.models.image_generation_model import ImageGenerationRequest
from app.services.generation_tracker import GenerationTracker
from app.services.image_generation_service import image_generation_service

router = APIRouter(prefix="/api/v1/canvas-actions", tags=["canvas-actions"])

# 文生图(无源图)的回退链
_IMAGE_CHAIN = ("dataeyes", "mige", "pollinations", "local")
# 图生图(有源图):只用真正读 image_urls(保真)的 DataEyes NanoBanana/Gemini 系模型,
# 跨多个模型回退以抗单模型 503;绝不降级到无视源图的 pollinations/local。
_I2I_MODELS = ("gemini-2.5-flash-image", "gemini-3-pro-image-preview", "gemini-2.5-flash-image-preview")

_canvas_action_tasks: dict[str, dict[str, Any]] = {}


class CanvasSelectionItem(BaseModel):
    nodeId: str
    assetId: str | None = None
    label: str | None = None
    type: str | None = None
    imageUrl: str | None = None


class CanvasActionRequest(BaseModel):
    project_id: int = Field(..., ge=1)
    instruction: str = Field(..., min_length=1)
    selection: list[CanvasSelectionItem] = Field(default_factory=list)


@router.post("")
async def start_canvas_action(req: CanvasActionRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    assert_generation_access(db, req.project_id, current_user)
    if not req.selection:
        raise HTTPException(status_code=400, detail="至少选择一个画布节点")

    task_id = str(uuid.uuid4())
    _canvas_action_tasks[task_id] = {"status": "processing"}
    gt = GenerationTracker.get()
    progress = gt.create(task_id, total_steps=3)

    async def run_action():
        try:
            source = req.selection[0]
            await progress.step("理解选区", "thinking", "读取所选节点和素材上下文")
            await progress.step("生成变体", "generating", "基于指令生成画布变体")
            generated_image_url, generated_asset_id = await generate_canvas_variant_asset(req, source)
            result = build_canvas_action_result(
                req,
                source,
                task_id,
                generated_image_url=generated_image_url,
                generated_asset_id=generated_asset_id,
            )
            await progress.step("回填画布", "generating", "准备新节点和关系边")
            await progress.done({"canvas_action": result})
            _canvas_action_tasks[task_id] = {"status": "complete", "result": result}
        except Exception as exc:
            await progress.error(str(exc))
            _canvas_action_tasks[task_id] = {"status": "error", "error": str(exc)}

    asyncio.create_task(run_action())
    return {"task_id": task_id, "status": "processing"}


@router.get("/{task_id}")
async def poll_canvas_action(task_id: str):
    if task_id not in _canvas_action_tasks:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    return _canvas_action_tasks[task_id]


async def generate_canvas_variant_asset(req: CanvasActionRequest, source: CanvasSelectionItem) -> tuple[str, str]:
    image_options: dict[str, Any] = {}
    is_i2i = bool(source.imageUrl)
    if is_i2i:
        image_options["image_urls"] = [source.imageUrl]

    # 编辑式提示词:引导模型尽量保留原图其它部分,只改用户要求处
    if is_i2i:
        gen_prompt = (
            "这是一张需要局部修改的图片。请在尽量保留原图整体构图、背景、主体姿态、"
            f"版式、品牌标识与文字的前提下,仅按以下要求修改:{req.instruction}。"
            "除明确要求外的部分保持与原图一致,不要改变其它元素。"
        )
    else:
        gen_prompt = req.instruction

    # 图生图(有源图):跨多个保真 i2i 模型回退(都读 image_urls);文生图:provider 回退链。
    # (provider, model) 列表
    if is_i2i:
        attempt_list = [("dataeyes", m) for m in _I2I_MODELS]
    else:
        attempt_list = [(p, "gemini-2.5-flash-image" if p == "dataeyes" else None) for p in _IMAGE_CHAIN]

    image_result = None
    last_err: Exception | None = None
    for prov, mdl in attempt_list:
        try:
            r = await image_generation_service.generate(ImageGenerationRequest(
                provider=prov,
                prompt=gen_prompt,
                model=mdl,
                width=1024,
                height=1024,
                options=image_options,
                project_id=req.project_id,  # O1: 落盘按项目分区(tenant 由 service 派生)
            ))
            if r.status == "succeeded" and r.images:
                image_result = r
                break
        except Exception as e:  # noqa: BLE001 — 换下一个模型 / provider
            last_err = e
            continue
    if image_result is None or not image_result.images:
        if is_i2i:
            raise RuntimeError(f"图生图暂不可用:支持图像编辑的服务(dataeyes)未响应,请稍后重试 ({last_err})")
        raise RuntimeError(f"图编辑生成失败:所有图像 provider 不可用 ({last_err})")
    image_url = image_result.images[0].url
    asset_plan = {
        "project_id": req.project_id,
        "modality": "image",
        "source": "canvas_action_img2img",
        "prompt": req.instruction,
        "images": [{"url": image_url, "label": f"{source.label or source.nodeId} · 变体"}],
        "canvas_action": {
            "source_node_id": source.nodeId,
            "source_asset_id": source.assetId,
            "source_image_url": source.imageUrl,
            "instruction": req.instruction,
        },
    }
    db = SessionLocal()
    try:
        record = save_asset_plan(
            db=db,
            project_id=req.project_id,
            asset_plan=asset_plan,
            model_used=image_result.images[0].provider_asset_id or "gemini-2.5-flash-image",
        )
        return image_url, str(record.id)
    finally:
        db.close()


def build_canvas_action_result(
    req: CanvasActionRequest,
    source: CanvasSelectionItem,
    task_id: str = "",
    generated_image_url: str | None = None,
    generated_asset_id: str | None = None,
) -> dict[str, Any]:
    source_node_id = source.nodeId
    stable_key = hashlib.sha1(f"{req.project_id}:{source_node_id}:{req.instruction}".encode("utf-8")).hexdigest()[:10]
    variant_id = f"variant-{source_node_id}-{stable_key}"
    source_asset_id = source.assetId or source_node_id
    variant_asset_id = generated_asset_id or f"{source_asset_id}-variant-{stable_key}"
    label = f"{source.label or source_node_id} · 变体"

    node = {
        "id": variant_id,
        "type": source.type or "key_visual",
        "label": label,
        "x": 0,
        "y": 0,
        "width": 260,
        "height": 180,
        "thumbnail_url": generated_image_url,
        "metadata": {
            "instruction": req.instruction,
            "provenance": {
                "parentNodeId": source_node_id,
                "assetId": variant_asset_id,
            },
        },
        "asset_ref": {
            "asset_id": variant_asset_id,
            "url": generated_image_url,
            "relation": "variant_of",
        },
    }
    edge = {
        "id": f"edge-{source_node_id}-{variant_id}",
        "source_id": source_node_id,
        "target_id": variant_id,
        "label": req.instruction,
        "relation_type": "variant_of",
        "metadata": {
            "relation_type": "variant_of",
            "instruction": req.instruction,
        },
    }
    return {"node": node, "edge": edge, "task_id": task_id}
