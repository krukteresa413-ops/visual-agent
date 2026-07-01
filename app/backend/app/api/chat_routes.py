"""对话 Agent 的 SSE 端点：POST /api/v1/chat，把 run_turn 接成流式事件。

事件 data 为自描述 JSON（前端 SSE 解析只读 data 行），形状对齐现有
sseToChatEventAdapter 契约（MoyagProgressEvent）：
  {type, status, message?, detail?{url}}
  - status=thinking            → 思考中
  - status=generating + detail.url → 一张生成图（前端落到消息/画布）
  - status=generating + message    → Agent 文字回复
  - type=done, status=done     → 结束
  - type=error, status=error   → 出错
本版为离散事件流（非逐 token）；逐 token 流式留作后续细化。
"""
import json
import logging
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agents.conversation.agent import run_turn
from app.db.session import get_db
from app.models.auth import User
from app.models.chat_conversation import ChatConversation
from app.services.auth_service import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    reference_image_url: Optional[str] = None
    project_id: Optional[int] = None
    canvas_id: Optional[int] = None


class SaveHistoryRequest(BaseModel):
    project_id: int
    canvas_id: Optional[int] = None
    messages: List[Any] = Field(default_factory=list)


def _sse(payload: dict) -> str:
    event_type = payload.get("type", "progress")
    return f"event: {event_type}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _seed_canvas_image(project_id, image_url, label="Main Image", canvas_id=None):
    """把一张生成图写进该 (project, canvas) 的画布；任何失败都不得打断对话流。"""
    if not project_id or not image_url:
        return
    try:
        from app.api.unified_generation_routes import _ensure_canvas_image_elements
        from app.db.session import SessionLocal
        db = SessionLocal()
        try:
            _ensure_canvas_image_elements(
                db, int(project_id),
                {"main_image": {"url": image_url, "goal": label}},
                canvas_id=canvas_id,
            )
        finally:
            db.close()
    except Exception:
        logger.exception("canvas seed failed (non-fatal)")


async def chat_event_stream(message: str, reference_image_url: Optional[str], project_id=None, canvas_id=None):
    """可独立测试的事件生成器：把 run_turn 的结果转成自描述 SSE 事件。"""
    yield _sse({"type": "progress", "status": "thinking", "message": "正在处理…"})
    try:
        result = await run_turn(message, reference_image_url)
    except Exception as exc:
        logger.error("chat run_turn error: %s", exc)
        yield _sse({"type": "error", "status": "error", "message": str(exc)})
        return
    for url in result.get("assets", []):
        _seed_canvas_image(project_id, url, canvas_id=canvas_id)
        yield _sse({"type": "progress", "status": "generating", "detail": {"url": url}})
    yield _sse({"type": "progress", "status": "generating", "message": result.get("reply", "")})
    yield _sse({"type": "done", "status": "done"})


@router.post("")
async def chat(req: ChatRequest):
    """POST /api/v1/chat —— 流式返回 Agent 一轮对话的事件。"""
    return StreamingResponse(
        chat_event_stream(req.message, req.reference_image_url, req.project_id, req.canvas_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── 图三: 对话历史持久化(租户隔离) ──────────────────────────────────────
# 画布 AI 对话原本只在内存(chatState), 关面板/刷新即丢。这里按 (tenant, project)
# 存整段会话快照, 挂载回填、整轮完成时保存。租户隔离: 一律按 current_user.tenant_id 过滤。

@router.get("/history")
def get_chat_history(
    project_id: int = Query(...),
    canvas_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    from app.services.canvas_service import (
        assert_canvas_access,
        assert_project_access,
        get_chat_conversation_for,
    )
    assert_project_access(db, project_id, current_user)
    if canvas_id is not None:
        guarded = assert_canvas_access(db, canvas_id, current_user)
        if guarded.project_id != project_id:
            raise HTTPException(status_code=404, detail="canvas not found in project")
    _canvas, conv = get_chat_conversation_for(db, project_id, current_user.tenant_id, canvas_id)
    if not conv:
        return {"messages": []}
    try:
        return {"messages": json.loads(conv.messages or "[]")}
    except (ValueError, TypeError):
        return {"messages": []}


@router.put("/history")
def save_chat_history(
    req: SaveHistoryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    from app.services.canvas_service import (
        assert_canvas_access,
        assert_project_access,
        get_chat_conversation_for,
    )
    assert_project_access(db, req.project_id, current_user)
    if req.canvas_id is not None:
        guarded = assert_canvas_access(db, req.canvas_id, current_user)
        if guarded.project_id != req.project_id:
            raise HTTPException(status_code=404, detail="canvas not found in project")
    payload = json.dumps(req.messages, ensure_ascii=False)
    _canvas, conv = get_chat_conversation_for(
        db, req.project_id, current_user.tenant_id, req.canvas_id, create=True
    )
    conv.messages = payload
    db.commit()
    return {"ok": True, "count": len(req.messages)}
