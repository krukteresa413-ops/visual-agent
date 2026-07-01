"""图三: 画布 AI 对话历史持久化。

Phase C.2 起: 每张 canvas 一行(canvas_id 为权威键, NOT NULL + UNIQUE); tenant_id 仍做租户隔离,
project_id 保留为冗余/回退。messages 存整段对话的 JSON 数组(与前端 chatState.messages 对齐),
关面板/刷新/切画布后可回填, 解决"对话不见了"。
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.sql import func

from app.db.session import Base


class ChatConversation(Base):
    __tablename__ = "chat_conversations"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True, nullable=True)
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Phase C.2: 对话归属画布。canvas_id 为权威键(NOT NULL + UNIQUE)
    canvas_id = Column(
        Integer, ForeignKey("canvases.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    # JSON 数组字符串: [{id, role, step, content, status, percent, assets}, ...]
    messages = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
