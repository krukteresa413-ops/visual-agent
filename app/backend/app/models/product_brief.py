from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.db.session import Base


class ProductBrief(Base):
    __tablename__ = "product_briefs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    tenant_id = Column(Integer, index=True, nullable=True)

    product_name = Column(String(255), nullable=False)
    category = Column(String(255), nullable=False)

    specifications = Column(Text, nullable=True)
    materials = Column(Text, nullable=True)
    selling_points = Column(Text, nullable=True)
    target_market = Column(Text, nullable=True)
    target_customer = Column(Text, nullable=True)
    usage_scenarios = Column(Text, nullable=True)
    brand_style = Column(Text, nullable=True)
    compliance_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
