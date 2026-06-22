from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


ProjectStatus = Literal["active", "draft", "archived"]


class ProductBriefBase(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=255, description="产品名称")
    category: str = Field(..., min_length=1, max_length=255, description="产品品类")

    specifications: List[str] = Field(default_factory=list, description="核心规格")
    materials: List[str] = Field(default_factory=list, description="材质")
    selling_points: List[str] = Field(default_factory=list, description="主要卖点")

    target_market: List[str] = Field(default_factory=list, description="目标市场")
    target_customer: List[str] = Field(default_factory=list, description="目标客户")
    usage_scenarios: List[str] = Field(default_factory=list, description="使用场景")

    brand_style: Optional[str] = Field(default=None, max_length=500, description="品牌风格")
    compliance_notes: List[str] = Field(default_factory=list, description="合规/禁用信息")

    @field_validator(
        "specifications",
        "materials",
        "selling_points",
        "target_market",
        "target_customer",
        "usage_scenarios",
        "compliance_notes",
        mode="before",
    )
    @classmethod
    def normalize_list_fields(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


class ProductBriefCreate(ProductBriefBase):
    pass


class ProductBriefOut(ProductBriefBase):
    pass


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="项目名称")
    tenant: str = Field(default="muyuanjia", min_length=1, max_length=255, description="租户/客户标识")
    description: Optional[str] = Field(default=None, max_length=2000, description="项目描述")

    product_brief: Optional[ProductBriefCreate] = Field(
        default=None,
        description="产品资料结构化信息，后续用于 Agent 生成视觉方案",
    )


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    tenant: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    status: Optional[ProjectStatus] = None
    product_brief: Optional[ProductBriefCreate] = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    tenant: str
    description: Optional[str] = None
    status: ProjectStatus = "active"
    created_at: datetime
    updated_at: datetime


class ProjectDetailOut(ProjectOut):
    product_brief: Optional[ProductBriefOut] = None


# 兼容旧代码：如果 app/api/projects.py 里 import 了 Project，也不会报错
Project = ProjectOut
