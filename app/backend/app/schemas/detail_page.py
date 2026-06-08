from pydantic import BaseModel
from typing import Optional

class DetailPageModule(BaseModel):
    order: int
    module_type: str
    title: str
    content_description: str
    visual_suggestion: str
    recommended_height_px: Optional[int] = None
    copywriting: Optional[str] = None
    data_source: Optional[str] = None

class DetailPagePlan(BaseModel):
    page_goal: str
    target_platform: str
    target_audience: str
    total_modules: int
    estimated_scroll_depth: str
    modules: list[DetailPageModule]
    design_notes: Optional[str] = None
