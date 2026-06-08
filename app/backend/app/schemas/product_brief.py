from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProductBriefBase(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=255)

    specifications: Optional[str] = None
    materials: Optional[str] = None
    selling_points: Optional[str] = None
    target_market: Optional[str] = None
    target_customer: Optional[str] = None
    usage_scenarios: Optional[str] = None
    brand_style: Optional[str] = None
    compliance_notes: Optional[str] = None


class ProductBriefCreate(ProductBriefBase):
    pass


class ProductBriefUpdate(BaseModel):
    product_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    category: Optional[str] = Field(default=None, min_length=1, max_length=255)

    specifications: Optional[str] = None
    materials: Optional[str] = None
    selling_points: Optional[str] = None
    target_market: Optional[str] = None
    target_customer: Optional[str] = None
    usage_scenarios: Optional[str] = None
    brand_style: Optional[str] = None
    compliance_notes: Optional[str] = None


class ProductBriefOut(ProductBriefBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
