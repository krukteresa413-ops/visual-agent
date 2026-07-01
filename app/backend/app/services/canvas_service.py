"""Phase C 中枢：把「project_id(+可选 canvas_id)」解析成具体的 Canvas / CanvasState /
ChatConversation，并自愈迁移窗口内老代码可能创建的 canvas_id=NULL 遗留行。

设计要点：
- resolve_canvas: 传了 canvas_id 用之，否则回退项目默认画布(最小 sort_order/id)，无则懒建。
- get_canvas_state_for / get_chat_conversation_for: 先按 canvas_id 查;查不到则采纳该项目
  canvas_id=NULL 的遗留行(设上 canvas_id),避免后续按 project_id 唯一约束冲突;仍无且 create=True 才新建。
- 单画布行为不变: 前端不传 canvas_id → 回退默认画布(每项目恰 1 张,已回填) → 命中同一行。
"""
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.models.canvas import Canvas
from app.models.canvas_state import CanvasState
from app.models.chat_conversation import ChatConversation

_DEFAULT_VIEWPORT = '{"x":0,"y":0,"scale":1}'


def get_or_create_default_canvas(db: Session, project_id: int, tenant_id: Optional[int] = None) -> Canvas:
    canvas = (
        db.query(Canvas)
        .filter(Canvas.project_id == project_id)
        .order_by(Canvas.sort_order, Canvas.id)
        .first()
    )
    if canvas is not None:
        return canvas
    if tenant_id is None:
        from app.models.project import Project
        proj = db.query(Project).filter(Project.id == project_id).first()
        tenant_id = proj.tenant_id if proj is not None else None
    canvas = Canvas(project_id=project_id, tenant_id=tenant_id, name="画布 1", sort_order=0)
    db.add(canvas)
    db.commit()
    db.refresh(canvas)
    return canvas


def resolve_canvas(db: Session, project_id: int, canvas_id: Optional[int] = None) -> Canvas:
    if canvas_id:
        canvas = db.query(Canvas).filter(Canvas.id == canvas_id).first()
        if canvas is not None:
            return canvas
    return get_or_create_default_canvas(db, project_id)


def get_canvas_state_for(
    db: Session, project_id: int, canvas_id: Optional[int] = None, create_defaults: bool = False
) -> Tuple[Canvas, Optional[CanvasState]]:
    """返回 (canvas, canvas_state)。自愈 canvas_id=NULL 遗留行;create_defaults=True 时无则建空画布。"""
    canvas = resolve_canvas(db, project_id, canvas_id)
    state = db.query(CanvasState).filter(CanvasState.canvas_id == canvas.id).first()
    if state is None:
        legacy = (
            db.query(CanvasState)
            .filter(CanvasState.project_id == project_id, CanvasState.canvas_id.is_(None))
            .first()
        )
        if legacy is not None:
            legacy.canvas_id = canvas.id
            db.commit()
            state = legacy
    if state is None and create_defaults:
        state = CanvasState(
            project_id=project_id,
            canvas_id=canvas.id,
            elements_json="[]",
            connections_json="[]",
            viewport_json=_DEFAULT_VIEWPORT,
        )
        db.add(state)
        db.commit()
        db.refresh(state)
    return canvas, state


def get_chat_conversation_for(
    db: Session, project_id: int, tenant_id: Optional[int], canvas_id: Optional[int] = None, create: bool = False
) -> Tuple[Canvas, Optional[ChatConversation]]:
    """返回 (canvas, chat_conversation)。自愈 canvas_id=NULL 遗留行;create=True 时无则建空对话。"""
    canvas = resolve_canvas(db, project_id, canvas_id)
    conv = db.query(ChatConversation).filter(ChatConversation.canvas_id == canvas.id).first()
    if conv is None:
        legacy = (
            db.query(ChatConversation)
            .filter(
                ChatConversation.project_id == project_id,
                ChatConversation.tenant_id == tenant_id,
                ChatConversation.canvas_id.is_(None),
            )
            .first()
        )
        if legacy is not None:
            legacy.canvas_id = canvas.id
            db.commit()
            conv = legacy
    if conv is None and create:
        conv = ChatConversation(
            tenant_id=tenant_id, project_id=project_id, canvas_id=canvas.id, messages="[]"
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
    return canvas, conv
