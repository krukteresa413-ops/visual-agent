import asyncio
import hashlib
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db.session import SessionLocal
from app.db.crud_visual_asset_v2 import save_asset_plan
from app.models.image_generation_model import ImageGenerationRequest
from app.services.generation_tracker import GenerationTracker
from app.services.image_generation_service import image_generation_service

router = APIRouter(prefix="/api/v1/canvas-actions", tags=["canvas-actions"])

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
async def start_canvas_action(req: CanvasActionRequest):
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
    if source.imageUrl:
        image_options["image_urls"] = [source.imageUrl]
    image_result = await image_generation_service.generate(ImageGenerationRequest(
        provider="dataeyes",
        prompt=req.instruction,
        model="gemini-2.5-flash-image",
        width=1024,
        height=1024,
        options=image_options,
    ))
    if image_result.status != "succeeded" or not image_result.images:
        raise RuntimeError("图编辑生成失败：未返回图片")
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
