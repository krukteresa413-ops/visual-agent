"""
Visual Asset Plan Pydantic Schema。
"""
from pydantic import BaseModel, ConfigDict


class VisualAssetPlanCreate(BaseModel):
    """创建 visual_asset_plan 记录"""
    model_config = ConfigDict(from_attributes=True)

    project_id: int
    main_image_json: str
    white_bg_json: str
    scene_images_json: str
    selling_points_json: str
    video_scripts_json: str
    ad_material_json: str


class VisualAssetPlanOut(BaseModel):
    """输出 visual_asset_plan 记录"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    main_image_json: str
    white_bg_json: str
    scene_images_json: str
    selling_points_json: str
    video_scripts_json: str
    ad_material_json: str
