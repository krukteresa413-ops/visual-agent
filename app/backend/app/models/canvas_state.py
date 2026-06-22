"""
CanvasState ORM model for Atelier Flow infinite canvas.
Stores elements, connections, and viewport state as JSON columns.
One row per project.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from app.db.session import Base


class CanvasState(Base):
    __tablename__ = "canvas_states"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )

    # JSON arrays: [{id, type, label, x, y, width, height, rotation, zIndex, hidden, locked, editableLayers, thumbnail_url, ...}]
    elements_json = Column(Text, nullable=False, default="[]", comment="Canvas elements JSON including phase5 engine fields: rotation, zIndex, hidden, locked, editableLayers")

    # JSON arrays: [{id, source_id, target_id, label}]
    connections_json = Column(Text, nullable=False, default="[]")

    # JSON object: {x, y, scale}
    viewport_json = Column(Text, nullable=False, default='{"x":0,"y":0,"scale":1}')

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
