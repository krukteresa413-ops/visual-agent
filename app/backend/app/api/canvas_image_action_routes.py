"""Canvas image action API — right-click image tools for infinite canvas."""
from datetime import datetime
from typing import Literal
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.atelier_canvas_routes import get_db
from app.models.canvas_state import CanvasState
from app.services.canvas_image_action_service import canvas_image_action_service

router = APIRouter(prefix="/api/v1/canvas", tags=["canvas-image-actions"])

CanvasImageAction = Literal["cutout"]

ACTION_LABELS = {
    "cutout": "抠图",
}


class CanvasImageActionRequest(BaseModel):
    project_id: int = Field(..., ge=1)
    asset_id: str = Field(..., min_length=1)
    action: CanvasImageAction
    image_url: str = Field(..., min_length=1)
    instruction: str = ""
    provider: str = "dataeyes"
    model: str | None = None


def _load_canvas_elements(db: Session, project_id: int) -> tuple[CanvasState, list[dict]]:
    state = db.query(CanvasState).filter(CanvasState.project_id == project_id).first()
    if not state:
        raise HTTPException(status_code=404, detail="canvas state not found")
    try:
        elements = json.loads(state.elements_json or "[]")
    except Exception:
        elements = []
    return state, elements


def _build_action_element(
    req: CanvasImageActionRequest,
    parent: dict,
    result: dict,
    instruction: str,
    version: int,
) -> dict:
    parent_meta = parent.get("metadata") or {}
    url = result.get("url") or req.image_url
    parent_width = float(parent.get("width") or result.get("width") or 280)
    return {
        "id": f"{req.asset_id}_{req.action}_v{version}",
        "type": parent.get("type") or "image",
        "label": f"{parent.get('label') or ACTION_LABELS[req.action]} v{version}",
        "x": float(parent.get("x") or 0) + parent_width + 40,
        "y": float(parent.get("y") or 0),
        "width": parent.get("width") or result.get("width") or 280,
        "height": parent.get("height") or result.get("height") or 280,
        "thumbnail_url": url,
        "asset_ref": {
            **(parent.get("asset_ref") or {}),
            "url": url,
            "parent_asset_id": req.asset_id,
            "version": version,
            "canvas_action": req.action,
        },
        "metadata": {
            **parent_meta,
            "url": url,
            "thumbnail_url": url,
            "parent_asset_id": req.asset_id,
            "version": version,
            "instruction": instruction,
            "canvas_action": req.action,
            "provider": result.get("provider"),
            "width": result.get("width"),
            "height": result.get("height"),
        },
    }


def _append_action_version(db: Session, req: CanvasImageActionRequest, result: dict, instruction: str) -> list[dict]:
    state, elements = _load_canvas_elements(db, req.project_id)
    parent = next((el for el in elements if el.get("id") == req.asset_id), None)
    if not parent:
        raise HTTPException(status_code=404, detail="selected asset not found")

    parent_meta = parent.get("metadata") or {}
    version = int(parent_meta.get("version") or 1) + 1
    canvas_element = _build_action_element(req, parent, result, instruction, version)

    elements.append(canvas_element)
    state.elements_json = json.dumps(elements, ensure_ascii=False)
    state.updated_at = datetime.utcnow()
    db.commit()
    return [canvas_element]


@router.post("/image-action")
async def run_canvas_image_action(req: CanvasImageActionRequest, db: Session = Depends(get_db)):
    instruction = req.instruction.strip() or ACTION_LABELS[req.action]
    try:
        result = await canvas_image_action_service.run(
            action=req.action,
            image_url=req.image_url,
            instruction=req.instruction.strip(),
            provider=req.provider,
            model=req.model,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="抠图处理失败") from exc

    canvas_elements = _append_action_version(db, req, result, instruction)
    return {"action": req.action, "modified": result, "canvas_element": canvas_elements[0], "canvas_elements": canvas_elements}
