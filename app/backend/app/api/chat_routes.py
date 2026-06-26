"""对话 Agent 的 SSE 端点：POST /api/v1/chat，把 run_turn 接成流式事件。

事件协议（SSE，event: <type> / data: <json>）：
  status — {message}   立即回执「正在处理」
  asset  — {url}       每生成一张图一个事件（前端可直接落到画布）
  reply  — {text}      Agent 的自然语言回复
  done   — {}          结束
  error  — {message}   出错
本版为离散事件流（非逐 token）；逐 token 流式留作后续细化。
"""
import json
import logging
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.agents.conversation.agent import run_turn

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    reference_image_url: Optional[str] = None


def _sse(event_type: str, data: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def chat_event_stream(message: str, reference_image_url: Optional[str]):
    """可独立测试的事件生成器：把 run_turn 的结果转成 SSE 事件。"""
    yield _sse("status", {"message": "正在处理…"})
    try:
        result = await run_turn(message, reference_image_url)
    except Exception as exc:
        logger.error("chat run_turn error: %s", exc)
        yield _sse("error", {"message": str(exc)})
        return
    for url in result.get("assets", []):
        yield _sse("asset", {"url": url})
    yield _sse("reply", {"text": result.get("reply", "")})
    yield _sse("done", {})


@router.post("")
async def chat(req: ChatRequest):
    """POST /api/v1/chat —— 流式返回 Agent 一轮对话的事件。"""
    return StreamingResponse(
        chat_event_stream(req.message, req.reference_image_url),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
