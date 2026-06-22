import asyncio
import hashlib
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.generation_tracker import GenerationTracker

router = APIRouter(prefix="/api/v1/canvas-actions", tags=["canvas-actions"])

_canvas_action_tasks: dict[str, dict[str, Any]] = {}


class CanvasSelectionItem(BaseModel):
    nodeId: str
    assetId: str | None = None
    label: str | None = None
    type: str | None = None


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
            result = build_canvas_action_result(req, source, task_id)
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


def build_canvas_action_result(req: CanvasActionRequest, source: CanvasSelectionItem, task_id: str = "") -> dict[str, Any]:
    source_node_id = source.nodeId
    stable_key = hashlib.sha1(f"{req.project_id}:{source_node_id}:{req.instruction}".encode("utf-8")).hexdigest()[:10]
    variant_id = f"variant-{source_node_id}-{stable_key}"
    source_asset_id = source.assetId or source_node_id
    variant_asset_id = f"{source_asset_id}-variant-{stable_key}"
    label = f"{source.label or source_node_id} · 变体"

    node = {
        "id": variant_id,
        "type": source.type or "key_visual",
        "label": label,
        "x": 0,
        "y": 0,
        "width": 260,
        "height": 180,
        "metadata": {
            "instruction": req.instruction,
            "provenance": {
                "parentNodeId": source_node_id,
                "assetId": variant_asset_id,
                "parentAssetId": source_asset_id,
            },
        },
        "asset_ref": {
            "asset_id": variant_asset_id,
            "parent_asset_id": source_asset_id,
            "relation": "variant_of",
        },
    }
    edge = {
        "id": f"edge-{source_node_id}-{variant_id}",
        "source_id": source_node_id,
        "target_id": variant_id,
        "label": "variant_of",
        "relation_type": "variant_of",
        "metadata": {
            "relation_type": "variant_of",
            "instruction": req.instruction,
        },
    }
    return {"node": node, "edge": edge, "task_id": task_id}
