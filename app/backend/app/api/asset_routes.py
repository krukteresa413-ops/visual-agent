"""Asset modify API — supports text, crop, and ChatCanvas image version operations."""
from typing import Optional
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.atelier_canvas_routes import get_db
from app.models.canvas_state import CanvasState
from app.models.image_generation_model import ImageGenerationRequest
from app.services.brand_memory_learner import BrandMemoryLearner
from app.services.image_generation_service import image_generation_service

router = APIRouter(prefix="/api/v1/asset", tags=["asset-modify"])

brand_learner = BrandMemoryLearner()

MODIFY_SYSTEM_PROMPT = """你是素材修改助手。你收到一个已生成的素材和一个修改指令，请根据指令修改素材内容。

规则：
1. 保持输出 JSON 结构完全不变，只修改内容
2. 只修改与指令相关的字段，其他字段保持不变
3. 修改后的内容应与产品信息一致
4. 严格输出 JSON，不要任何额外文字"""


class CropRegion(BaseModel):
    x: int
    y: int
    width: int
    height: int


class ModifyRequest(BaseModel):
    asset_type: str
    original: dict
    instruction: str
    brief: dict
    operation: str = "text"
    crop_region: Optional[CropRegion] = None
    project_id: Optional[int] = None
    canvas_id: Optional[int] = None
    asset_id: Optional[str] = None
    provider: str = "dataeyes"
    model: Optional[str] = None


def _append_canvas_version(
    db: Session,
    project_id: int,
    parent_asset_id: str,
    original: dict,
    modified: dict,
    asset_type: str,
    instruction: str,
    canvas_id: Optional[int] = None,
) -> dict:
    from app.services.canvas_service import get_canvas_state_for
    _canvas, state = get_canvas_state_for(db, project_id, canvas_id)
    if not state:
        raise HTTPException(status_code=404, detail="canvas state not found")

    try:
        elements = json.loads(state.elements_json or "[]")
    except Exception:
        elements = []

    parent = next((el for el in elements if el.get("id") == parent_asset_id), None)
    if not parent:
        raise HTTPException(status_code=404, detail="selected asset not found")

    parent_meta = parent.get("metadata") or original or {}
    parent_version = int(parent_meta.get("version") or 1)
    version = parent_version + 1
    url = modified.get("url") or modified.get("thumbnail_url") or parent.get("thumbnail_url")
    new_element = {
        "id": f"{parent_asset_id}_v{version}",
        "type": parent.get("type") or asset_type,
        "label": f"{parent.get('label') or '素材'} v{version}",
        "x": float(parent.get("x") or 0) + float(parent.get("width") or 280) + 40,
        "y": float(parent.get("y") or 0),
        "width": parent.get("width") or 280,
        "height": parent.get("height") or 280,
        "thumbnail_url": url,
        "asset_ref": {
            **(parent.get("asset_ref") or {}),
            "url": url,
            "parent_asset_id": parent_asset_id,
            "version": version,
        },
        "metadata": {
            **modified,
            "url": url,
            "thumbnail_url": url,
            "parent_asset_id": parent_asset_id,
            "version": version,
            "instruction": instruction,
        },
    }
    elements.append(new_element)
    state.elements_json = json.dumps(elements, ensure_ascii=False)
    state.updated_at = datetime.utcnow()
    db.commit()
    return new_element


async def _generate_image_version(req: ModifyRequest) -> dict:
    original_prompt = (
        req.original.get("prompt")
        or req.original.get("goal")
        or req.original.get("scene_narrative")
        or ""
    )
    prompt = (
        "基于原图/原素材进行局部修改，保持商品主体不变。\n"
        f"原始描述: {original_prompt}\n"
        f"修改指令: {req.instruction}"
    )
    result = await image_generation_service.generate(ImageGenerationRequest(
        provider=req.provider,
        model=req.model,
        prompt=prompt,
        width=1024,
        height=1024,
    ))
    image = result.images[0] if result.images else None
    if not image or not image.url:
        raise HTTPException(status_code=502, detail="image modification returned no url")

    modified = dict(req.original)
    modified.update({
        "prompt": prompt,
        "url": image.url,
        "thumbnail_url": image.url,
        "width": image.width,
        "height": image.height,
        "status": "succeeded",
    })
    return modified


@router.post("/modify")
async def modify_asset(req: ModifyRequest, db: Session = Depends(get_db)):
    """根据自然语言指令或 crop 操作修改素材内容。"""
    if not req.instruction.strip():
        return {"modified": req.original}

    if req.operation == "crop" and req.crop_region:
        modified = dict(req.original)
        modified["_crop"] = req.crop_region.model_dump()
        modified["_crop_instruction"] = req.instruction
        return {"modified": modified}

    if req.project_id and req.asset_id and req.asset_type in {"image", "main_image", "white_bg", "scene_image", "key_visual"}:
        modified = await _generate_image_version(req)
        modified["parent_asset_id"] = req.asset_id
        modified["version"] = int(req.original.get("version") or 1) + 1
        canvas_element = _append_canvas_version(
            db=db,
            project_id=req.project_id,
            parent_asset_id=req.asset_id,
            original=req.original,
            modified=modified,
            asset_type=req.asset_type,
            instruction=req.instruction,
            canvas_id=req.canvas_id,
        )
        return {"modified": modified, "canvas_element": canvas_element}

    from app.api.unified_generation_routes import agent

    try:
        user_prompt = f"""## 产品信息
{req.brief}

## 当前素材
```json
{req.original}
```

## 修改指令
{req.instruction}

请输出修改后的 JSON（保持结构不变）："""
        modified = await agent._llm.call(
            system_prompt=MODIFY_SYSTEM_PROMPT,
            user_prompt=str(user_prompt),
            temperature=0.7,
        )

        try:
            await brand_learner.learn_from_edit(
                project_id=req.brief.get("project_id", 0),
                edit_type="text",
                before=str(req.instruction),
                after=str(modified),
            )
        except Exception:
            pass

        return {"modified": modified}
    except Exception as e:
        return {"modified": req.original, "error": str(e)}
