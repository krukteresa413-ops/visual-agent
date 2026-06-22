"""
灵感库 — InspirationItem ORM 模型。
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from app.db.session import Base


class InspirationItem(Base):
    __tablename__ = "inspiration_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    category = Column(String(50), nullable=False, index=True)         # poster / app / illustration / ops / ip
    sub_category = Column(String(100), nullable=False)                # 拼贴海报 / App 图标 / 黏土 …
    preview_url = Column(String(1024), nullable=False)                # OSS 图片 URL
    prompt_template = Column(Text, nullable=False)                    # 可参数化的 Prompt 模板
    aspect_ratio = Column(String(20), nullable=True)                  # 1 / 1 或 9 / 16
    source = Column(String(50), nullable=True, default="image2_seed")  # 数据来源标记

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
