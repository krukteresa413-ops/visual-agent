"""
视觉素材输出 Schema。
严格对照 PRD 第8章和第10章定义。
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, ConfigDict, field_validator


class MainImagePlan(BaseModel):
    """PRD 8.3 — 主图生成方案"""
    model_config = ConfigDict(from_attributes=True)

    asset_type: Literal["main_image"]
    goal: str
    composition: str
    background: str
    lighting: Optional[str] = None
    copywriting: Optional[str] = None
    prompt: str
    negative_prompt: Optional[str] = None
    platform: Optional[str] = None
    status: str = "draft"


class WhiteBgPlan(BaseModel):
    """PRD 8.4 — 白底图方案"""
    model_config = ConfigDict(from_attributes=True)

    asset_type: Literal["white_bg"] = "white_bg"
    goal: str
    instructions: str
    quality_checklist: Optional[List[str]] = None
    status: str = "draft"


class SceneImagePlan(BaseModel):
    """PRD 8.5 — 场景图方案"""
    model_config = ConfigDict(from_attributes=True)

    scene_name: str
    target_user: str
    scene_narrative: str
    visual_elements: List[str]
    product_position: str
    prompt: str
    negative_prompt: Optional[str] = None


class SellingPointModule(BaseModel):
    """PRD 8.6 — 卖点图模块"""
    model_config = ConfigDict(from_attributes=True)

    title: str
    description: str
    visual_representation: str
    icon_suggestion: str
    layout_suggestion: str


class StoryboardShot(BaseModel):
    """分镜单镜头"""
    shot_number: Optional[int] = None
    duration: Optional[str] = None
    visual: Optional[str] = None
    subtitle: Optional[str] = None
    voiceover: Optional[str] = None


class VideoScript(BaseModel):
    """PRD 8.7 — 短视频脚本"""
    model_config = ConfigDict(from_attributes=True)

    video_goal: str
    duration_seconds: Literal[15, 30]
    storyboard: List[StoryboardShot]
    cta: str
    material_requirements: List[str]
    pacing: str

    @field_validator("duration_seconds")
    @classmethod
    def validate_duration(cls, v):
        if v not in (15, 30):
            raise ValueError("PRD要求只支持15秒和30秒脚本")
        return v


class AdMaterialPlan(BaseModel):
    """PRD 8.8 — 广告视频素材方案"""
    model_config = ConfigDict(from_attributes=True)

    ad_goal: str
    target_audience: str
    ad_angle: str
    material_list: List[str]
    shot_sequence: List[str]
    hook: str
    key_selling_points: List[str]
    cta: str
    platform_suggestion: str


class VisualAssetPlanOut(BaseModel):
    """聚合输出 — PRD 5.1 六类素材全覆盖"""
    model_config = ConfigDict(from_attributes=True)

    project_id: int
    main_image: MainImagePlan
    white_bg: WhiteBgPlan
    scene_images: List[SceneImagePlan]
    selling_points: List[SellingPointModule]
    video_scripts: List[VideoScript]
    ad_material: AdMaterialPlan
    layout_plan: Optional[dict] = None
