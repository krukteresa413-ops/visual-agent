"""
品牌套件输出模型。
"""
from pydantic import BaseModel
from typing import Optional


class BrandKitOut(BaseModel):
    brand_name: str
    tagline: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    font_headings: Optional[str] = None
    font_body: Optional[str] = None
    tone_of_voice: Optional[str] = None
    visual_style: Optional[str] = None
    iconography: Optional[str] = None
    brand_story: Optional[str] = None
