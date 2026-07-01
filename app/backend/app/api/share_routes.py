"""真·分享端点（Phase S）。

- POST /api/v1/share      (需登录) 冻结当前 project 画布为快照, 建 token, 返回 token。
- GET  /api/v1/share/{token} (免登录) 返回冻结快照, 供 /share/:token 只读页渲染。
- DELETE /api/v1/share/{token} (需登录) 撤销(软删)。

快照 = 分享那一刻的画布拷贝, 之后编辑不影响已分享内容; 只暴露画布视觉, 不含租户其它数据。
"""
import json
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.auth import User
from app.models.canvas_state import CanvasState
from app.models.project import Project
from app.models.share_link import ShareLink
from app.services.auth_service import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/share", tags=["share"])

_DEFAULT_VIEWPORT = {"x": 0, "y": 0, "scale": 1}


class CreateShareRequest(BaseModel):
    project_id: int
    title: Optional[str] = None


def _loads(raw, default):
    try:
        return json.loads(raw) if raw else default
    except (ValueError, TypeError):
        return default


def _load_canvas_snapshot(db: Session, project_id: int) -> dict:
    """读取该 project 的画布状态并冻结为 {elements, connections, viewport}。"""
    cs = (
        db.query(CanvasState)
        .filter(CanvasState.project_id == project_id)
        .first()
    )
    if not cs:
        return {"elements": [], "connections": [], "viewport": dict(_DEFAULT_VIEWPORT)}
    return {
        "elements": _loads(cs.elements_json, []),
        "connections": _loads(cs.connections_json, []),
        "viewport": _loads(cs.viewport_json, dict(_DEFAULT_VIEWPORT)),
    }


@router.post("")
def create_share(
    req: CreateShareRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    project = db.query(Project).filter(Project.id == req.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="project not found")
    # 租户守卫: 只能分享本公司(tenant)的项目
    if (
        project.tenant_id is not None
        and current_user.tenant_id is not None
        and project.tenant_id != current_user.tenant_id
    ):
        raise HTTPException(status_code=403, detail="forbidden")

    canvas = _load_canvas_snapshot(db, req.project_id)
    snapshot = {"canvas": canvas, "meta": {"project_name": project.name}}
    token = uuid.uuid4().hex
    link = ShareLink(
        token=token,
        project_id=req.project_id,
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        scope="public",
        title=(req.title or project.name),
        snapshot_json=json.dumps(snapshot, ensure_ascii=False),
    )
    db.add(link)
    db.commit()
    element_count = len(canvas.get("elements") or [])
    return {"token": token, "title": link.title, "element_count": element_count}


@router.get("/{token}")
def get_share(token: str, db: Session = Depends(get_db)) -> dict:
    """免登录只读: 持 token 即可取冻结快照。"""
    link = (
        db.query(ShareLink)
        .filter(ShareLink.token == token, ShareLink.revoked.is_(False))
        .first()
    )
    if not link:
        raise HTTPException(status_code=404, detail="share not found")
    snapshot = _loads(link.snapshot_json, {})
    canvas = snapshot.get("canvas") or {
        "elements": [],
        "connections": [],
        "viewport": dict(_DEFAULT_VIEWPORT),
    }
    return {
        "title": link.title,
        "created_at": link.created_at.isoformat() if link.created_at else None,
        "canvas": canvas,
        "meta": snapshot.get("meta") or {},
    }


@router.delete("/{token}")
def revoke_share(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    link = db.query(ShareLink).filter(ShareLink.token == token).first()
    if not link:
        raise HTTPException(status_code=404, detail="share not found")
    if (
        link.tenant_id is not None
        and current_user.tenant_id is not None
        and link.tenant_id != current_user.tenant_id
    ):
        raise HTTPException(status_code=403, detail="forbidden")
    link.revoked = True
    db.commit()
    return {"ok": True}
