"""Font generation data models - SQLAlchemy ORM + Pydantic schemas."""
from typing import Optional, Literal
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from pydantic import BaseModel, Field

from app.db.session import Base


# ---------------------------------------------------------------------------
# SQLAlchemy ORM Model (Database)
# ---------------------------------------------------------------------------

class FontGeneration(Base):
    """Font generation task record."""
    
    __tablename__ = "font_generations"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(255), unique=True, nullable=False, index=True)
    text = Column(Text, nullable=False)  # 要生成的文字内容
    style_name = Column(String(255), nullable=True)  # 字体风格名称
    status = Column(String(50), nullable=False, default="pending")  # pending, processing, completed, failed
    image_url = Column(Text, nullable=True)  # 生成的字体图片URL
    provider = Column(String(50), nullable=False, default="mige")  # mige, zi2zi
    error_message = Column(Text, nullable=True)  # 错误信息（如果失败）
    
    # Metadata
    prompt = Column(Text, nullable=True)  # 生成时使用的完整prompt
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    generation_seconds = Column(Integer, nullable=True)  # 生成耗时（秒）
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


# ---------------------------------------------------------------------------
# Pydantic Models (API Request/Response)
# ---------------------------------------------------------------------------

FontProviderKind = Literal["mige", "zi2zi"]


class FontGenerationRequest(BaseModel):
    """Request to generate font images."""
    
    text: str = Field(..., min_length=1, max_length=1000, description="要生成的文字内容")
    style_name: Optional[str] = Field(None, max_length=255, description="字体风格名称（如：优雅宋体、现代黑体）")
    provider: FontProviderKind = Field("mige", description="生成提供商：mige (Phase 1) 或 zi2zi (Phase 2)")
    
    # Optional generation parameters
    width: int = Field(default=1024, ge=64, le=2048)
    height: int = Field(default=1024, ge=64, le=2048)

    # OSS 多租户分区(Phase O1)：可选携带；字体路由目前无 auth/project → 通常 None → shared/font。
    project_id: Optional[int] = None
    tenant_id: Optional[int] = None


class FontGenerationResponse(BaseModel):
    """Response after submitting font generation task."""
    
    task_id: str
    status: str  # pending, processing
    text: str
    style_name: Optional[str] = None
    provider: str
    created_at: datetime


class FontGenerationResult(BaseModel):
    """Font generation task result (after completion)."""
    
    model_config = {"from_attributes": True}
    
    id: int
    task_id: str
    text: str
    style_name: Optional[str] = None
    status: str  # completed, failed
    image_url: Optional[str] = None
    error_message: Optional[str] = None
    provider: str
    generation_seconds: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class FontHistoryResponse(BaseModel):
    """Paginated font generation history."""
    
    items: list[FontGenerationResult]
    total: int
    page: int
    page_size: int
    total_pages: int
