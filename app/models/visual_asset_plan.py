"""
Visual Asset Plan 数据库模型。
存储 LLM 生成的六类视觉素材方案。
"""
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.db.session import Base


class VisualAssetPlan(Base):
    __tablename__ = "visual_asset_plans"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)

    main_image_json = Column(Text, nullable=False)
    white_bg_json = Column(Text, nullable=False)
    scene_images_json = Column(Text, nullable=False)
    selling_points_json = Column(Text, nullable=False)
    video_scripts_json = Column(Text, nullable=False)
    ad_material_json = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
