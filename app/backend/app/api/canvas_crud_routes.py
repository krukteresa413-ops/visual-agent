"""Phase C Step 2：Canvas CRUD —— 一项目多画布的增删改查, 全租户守卫。

  GET    /api/v1/projects/{project_id}/canvases   列该项目全部 canvas(按 sort_order,id)
  POST   /api/v1/projects/{project_id}/canvases   新建 canvas(= 新建对话/新画布), 返回新行
  PATCH  /api/v1/canvases/{canvas_id}             重命名 / 排序
  DELETE /api/v1/canvases/{canvas_id}             删(禁止删项目最后一张)

全部经 get_current_user 鉴权 + assert_project_access/assert_canvas_access 租户守卫。
删除时显式级联清理该 canvas 的 canvas_state / chat_conversation(不依赖 DB FK 配置)。
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.auth import User
from app.models.canvas import Canvas
from app.models.canvas_state import CanvasState
from app.models.chat_conversation import ChatConversation
from app.services.auth_service import get_current_user
from app.services.canvas_service import (
    assert_canvas_access,
    assert_project_access,
    get_or_create_default_canvas,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["canvas-crud"])


class CanvasCreateRequest(BaseModel):
    name: Optional[str] = None


class CanvasUpdateRequest(BaseModel):
    name: Optional[str] = None
    sort_order: Optional[int] = None


def _serialize(c: Canvas) -> dict:
    return {
        "id": c.id,
        "project_id": c.project_id,
        "name": c.name,
        "sort_order": c.sort_order,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


@router.get("/projects/{project_id}/canvases")
def list_canvases(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """列该项目全部 canvas。若项目从无画布 → 懒建默认, 保证 UI 至少 1 张(对齐 resolve_canvas)。"""
    assert_project_access(db, project_id, current_user)
    canvases = (
        db.query(Canvas)
        .filter(Canvas.project_id == project_id)
        .order_by(Canvas.sort_order, Canvas.id)
        .all()
    )
    if not canvases:
        canvases = [get_or_create_default_canvas(db, project_id)]
    return {"canvases": [_serialize(c) for c in canvases]}


@router.post("/projects/{project_id}/canvases")
def create_canvas(
    project_id: int,
    req: CanvasCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """新建一张 canvas。sort_order = 现有 max + 1; 名字缺省 = "画布 N"。"""
    project = assert_project_access(db, project_id, current_user)
    existing = (
        db.query(Canvas)
        .filter(Canvas.project_id == project_id)
        .order_by(Canvas.sort_order.desc(), Canvas.id.desc())
        .first()
    )
    next_order = (existing.sort_order + 1) if existing is not None else 0
    count = db.query(Canvas).filter(Canvas.project_id == project_id).count()
    name = (req.name or "").strip() or f"画布 {count + 1}"
    canvas = Canvas(
        project_id=project_id,
        tenant_id=project.tenant_id,
        name=name,
        sort_order=next_order,
    )
    db.add(canvas)
    db.commit()
    db.refresh(canvas)
    return _serialize(canvas)


@router.patch("/canvases/{canvas_id}")
def update_canvas(
    canvas_id: int,
    req: CanvasUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """重命名 / 调整排序。空名忽略(不清空)。"""
    canvas = assert_canvas_access(db, canvas_id, current_user)
    if req.name is not None:
        new_name = req.name.strip()
        if new_name:
            canvas.name = new_name
    if req.sort_order is not None:
        canvas.sort_order = req.sort_order
    db.commit()
    db.refresh(canvas)
    return _serialize(canvas)


@router.delete("/canvases/{canvas_id}")
def delete_canvas(
    canvas_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """删 canvas。禁止删项目最后一张(保证项目 ≥1 画布)。
    显式级联删其 canvas_state / chat_conversation, 不依赖 DB FK 是否配了 ON DELETE CASCADE。"""
    canvas = assert_canvas_access(db, canvas_id, current_user)
    remaining = db.query(Canvas).filter(Canvas.project_id == canvas.project_id).count()
    if remaining <= 1:
        raise HTTPException(status_code=400, detail="不能删除项目的最后一张画布")
    db.query(CanvasState).filter(CanvasState.canvas_id == canvas_id).delete(synchronize_session=False)
    db.query(ChatConversation).filter(ChatConversation.canvas_id == canvas_id).delete(synchronize_session=False)
    db.delete(canvas)
    db.commit()
    return {"ok": True, "deleted": canvas_id}
