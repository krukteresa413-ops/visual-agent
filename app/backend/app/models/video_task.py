"""Video task persistence model (P2-11 gap).

Replaces in-memory polling — tasks survive service restart.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.sql import func

from app.db.session import Base


class VideoTask(Base):
    __tablename__ = "video_tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    vendor = Column(String(30), nullable=False, index=True)          # seedance/kling/hailuo/vidu/jimeng/grok
    provider_task_id = Column(String(255), nullable=False, index=True)  # remote task id
    model = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="submitted")  # submitted/polling/succeeded/failed
    prompt = Column(Text, nullable=False)
    duration = Column(Integer, default=5)
    options_json = Column(Text, nullable=True)                        # JSON: extra params
    video_url = Column(String(1024), nullable=True)                   # Downloaded URL
    local_path = Column(String(1024), nullable=True)                  # Local file path
    project_id = Column(Integer, nullable=True, index=True)
    canvas_node_id = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    poll_count = Column(Integer, default=0)
    cost_ticks = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
