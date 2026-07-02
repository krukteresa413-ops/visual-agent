"""真·分享端点（Phase S）。

- POST /api/v1/share      (需登录) 冻结当前 project 画布为快照, 建 token, 返回 token。
- GET  /api/v1/share/{token} (免登录) 返回冻结快照, 供 /share/:token 只读页渲染。
- DELETE /api/v1/share/{token} (需登录) 撤销(软删)。

快照 = 分享那一刻的画布拷贝, 之后编辑不影响已分享内容; 只暴露画布视觉, 不含租户其它数据。
"""
import json
import logging
import uuid
from typing import Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.auth import User
from app.models.canvas import Canvas
from app.models.project import Project
from app.models.share_link import ShareLink
from app.services.auth_service import get_current_user
from app.services.canvas_service import assert_generation_access, get_canvas_state_for, tenant_access_denied

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/share", tags=["share"])

_DEFAULT_VIEWPORT = {"x": 0, "y": 0, "scale": 1}


class CreateShareRequest(BaseModel):
    project_id: int
    # Phase C ③: 分享按 canvas —— 冻结指定画布快照; 缺省回退项目默认画布(向后兼容旧前端)
    canvas_id: Optional[int] = None
    title: Optional[str] = None


def _loads(raw, default):
    try:
        return json.loads(raw) if raw else default
    except (ValueError, TypeError):
        return default


def _load_canvas_snapshot(
    db: Session, project_id: int, canvas_id: Optional[int] = None
) -> Tuple[Canvas, dict]:
    """解析目标画布(传 canvas_id 用之, 否则项目默认画布), 冻结其状态为
    {elements, connections, viewport}。返回 (canvas, snapshot)。

    Phase C 前是按 project_id 取唯一 CanvasState; C.2 后 project_id 不再唯一
    (一项目 N 张画布 = N 行 state), 必须经 canvas_service 中枢按具体 canvas 取,
    否则 .first() 会冻结到任意/默认画布(在非默认画布上分享 → 冻错画布)。
    """
    canvas, cs = get_canvas_state_for(db, project_id, canvas_id)
    if not cs:
        return canvas, {"elements": [], "connections": [], "viewport": dict(_DEFAULT_VIEWPORT)}
    return canvas, {
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
    # 租户守卫 + canvas 归属校验(复用 Phase C ② 安全 pass 的统一守卫):
    # 项目须属当前租户; 传了 canvas_id 则该 canvas 须属当前租户且属于该 project
    # (跨项目/跨租户 canvas_id → 404/403, 不再静默回退到默认画布)。
    assert_generation_access(db, req.project_id, current_user, req.canvas_id)
    project = db.query(Project).filter(Project.id == req.project_id).first()

    canvas, canvas_snapshot = _load_canvas_snapshot(db, req.project_id, req.canvas_id)
    snapshot = {
        "canvas": canvas_snapshot,
        "meta": {"project_name": project.name, "canvas_name": canvas.name},
    }
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
    element_count = len(canvas_snapshot.get("elements") or [])
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
    if tenant_access_denied(link.tenant_id, getattr(current_user, "tenant_id", None)):  # O3: 统一走 flag 守卫
        raise HTTPException(status_code=403, detail="forbidden")
    link.revoked = True
    db.commit()
    return {"ok": True}
