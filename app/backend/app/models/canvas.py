"""Canvas ORM model — Phase C: 一个 Project 下可挂多张 Canvas。

每张 Canvas = 一个无限画布工作面(其 CanvasState) + 一段对话(其 ChatConversation)。
Project 仍是顶层分组;VisualAsset 素材库仍为 project 级共享,不随 canvas 拆分。
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.db.session import Base


class Canvas(Base):
    __tablename__ = "canvases"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    # 冗余租户列,用于租户守卫(对齐 chat_conversations 的做法);可空以兼容 tenant_id 未回填的老项目
    tenant_id = Column(Integer, index=True, nullable=True)
    name = Column(String(255), nullable=False, default="画布 1")
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
