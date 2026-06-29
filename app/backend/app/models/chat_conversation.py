"""图三: 画布 AI 对话历史持久化(按 tenant+project 的会话快照)。

多租户第一块持久化数据: tenant_id 做隔离。每个 (tenant, project) 一行,
messages 存整段对话的 JSON 数组(与前端 chatState.messages 对齐),
关面板/刷新/切项目后可回填, 解决"对话不见了"。
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.sql import func

from app.db.session import Base


class ChatConversation(Base):
    __tablename__ = "chat_conversations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "project_id", name="uq_chat_conv_tenant_project"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True, nullable=True)
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # JSON 数组字符串: [{id, role, step, content, status, percent, assets}, ...]
    messages = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
