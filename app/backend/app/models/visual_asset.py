"""
视觉素材生成结果持久化模型。
每次 generate_all 调用产生一条记录。
"""
import json
from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, String
from app.db.session import Base
from app.models.project import Project
from app.models.product_brief import ProductBrief


class VisualAsset(Base):
    __tablename__ = "visual_assets"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    brief_id = Column(Integer, ForeignKey("product_briefs.id"), nullable=True)

    asset_plan_json = Column(Text, nullable=False)
    model_used = Column(String(100), nullable=True)
    generation_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def asset_plan(self) -> dict:
        return json.loads(self.asset_plan_json)

    @asset_plan.setter
    def asset_plan(self, value: dict):
        self.asset_plan_json = json.dumps(value, ensure_ascii=False)
