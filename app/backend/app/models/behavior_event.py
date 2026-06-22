"""
BehaviorEvent ORM model — tracks user actions for aesthetic calibration.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.session import Base


class BehaviorEvent(Base):
    __tablename__ = "behavior_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    generation_id = Column(Integer, nullable=True, index=True)  # VisualAsset id
    event_type = Column(String(50), nullable=False, index=True)  # exported, modified, regenerated, finalized, viewed
    image_path = Column(String(500), nullable=True)
    ai_score = Column(Float, nullable=True)  # AI aesthetic score at time of event
    metadata_json = Column(Text, nullable=True)  # extra context as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Indexes for common queries
    __table_args__ = (
        # Composite index for calibration queries
        {"sqlite_autoincrement": True},
    )
